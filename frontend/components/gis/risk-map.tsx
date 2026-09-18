"use client";

import { useMemo, useState } from "react";
import Map, { Layer, Marker, Popup, Source } from "react-map-gl/maplibre";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import type { GisLocation, SeverityLevel } from "@/types";

const riskColors: Record<SeverityLevel, string> = {
  critical: "#8a1f1f",
  high: "#dc4545",
  medium: "#f39a18",
  low: "#21965f",
};

const zoneRadii: Record<SeverityLevel, number> = {
  critical: 2.6,
  high: 2.2,
  medium: 1.6,
  low: 1.3,
};

const mapStyle: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [
    {
      id: "osm",
      type: "raster",
      source: "osm",
    },
  ],
};

function circlePolygon(
  center: [number, number],
  radiusKm: number,
  points = 64
): GeoJSON.Feature<GeoJSON.Polygon> {
  const coords: [number, number][] = [];
  const latPerKm = 1 / 111;
  const lngPerKm = 1 / (111 * Math.cos((center[1] * Math.PI) / 180));

  for (let i = 0; i < points; i++) {
    const angle = (i / points) * 2 * Math.PI;
    coords.push([
      center[0] + radiusKm * lngPerKm * Math.cos(angle),
      center[1] + radiusKm * latPerKm * Math.sin(angle),
    ]);
  }

  coords.push(coords[0]);

  return {
    type: "Feature",
    properties: {},
    geometry: {
      type: "Polygon",
      coordinates: [coords],
    },
  };
}

// GisLocation.position is [latitude, longitude]; MapLibre and GeoJSON
// expect [longitude, latitude].
function toLngLat(position: [number, number]): [number, number] {
  return [position[1], position[0]];
}

export function RiskMap({ locations }: { locations: GisLocation[] }) {
  const [popup, setPopup] = useState<GisLocation | null>(null);

  const zones = useMemo(
    () =>
      locations.map((location) => ({
        feature: {
          ...circlePolygon(toLngLat(location.position), zoneRadii[location.risk]),
          properties: { risk: location.risk },
        },
        color: riskColors[location.risk],
        risk: location.risk,
      })),
    [locations]
  );

  const zoneSource = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: zones.map(({ feature }) => feature),
    }),
    [zones]
  );

  return (
    <Map
      mapLib={maplibregl}
      initialViewState={{
        longitude: 73.8955,
        latitude: 18.5505,
        zoom: 11.5,
      }}
      style={{ width: "100%", height: "100%" }}
      mapStyle={mapStyle}
    >
      <Source id="risk-zones" type="geojson" data={zoneSource}>
        <Layer
          id="risk-zones-fill"
          type="fill"
          paint={{
            "fill-color": [
              "match",
              ["get", "risk"],
              "critical",
              riskColors.critical,
              "high",
              riskColors.high,
              "medium",
              riskColors.medium,
              riskColors.low,
            ],
            "fill-opacity": 0.18,
          }}
        />
        <Layer
          id="risk-zones-outline"
          type="line"
          paint={{
            "line-color": [
              "match",
              ["get", "risk"],
              "critical",
              riskColors.critical,
              "high",
              riskColors.high,
              "medium",
              riskColors.medium,
              riskColors.low,
            ],
            "line-width": 1.5,
          }}
        />
      </Source>

      {locations.map((location) => {
        const lngLat = toLngLat(location.position);
        return (
          <Marker
            key={location.name}
            longitude={lngLat[0]}
            latitude={lngLat[1]}
            anchor="center"
            onClick={(e) => {
              e.originalEvent.stopPropagation();
              setPopup(location);
            }}
          >
            <div className="flex h-5 w-5 cursor-pointer items-center justify-center rounded-full border-2 border-white shadow">
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: riskColors[location.risk] }}
              />
            </div>
          </Marker>
        );
      })}

      {popup && (
        <Popup
          longitude={toLngLat(popup.position)[0]}
          latitude={toLngLat(popup.position)[1]}
          anchor="top"
          closeButton={true}
          onClose={() => setPopup(null)}
          offset={10}
        >
          <div className="space-y-0.5 text-xs">
            <strong className="block text-sm">{popup.name}</strong>
            <span className="block">Risk Score: {popup.score}%</span>
            <span className="block">
              Risk Level:{" "}
              {popup.risk.charAt(0).toUpperCase() + popup.risk.slice(1)}
            </span>
            <span className="block">Nearby Cases: {popup.cases}</span>
            <span className="block">Prediction: {popup.window}</span>
            {popup.confidence !== undefined && (
              <span className="block">
                Confidence: {Math.round(popup.confidence * 100)}%
              </span>
            )}
            {popup.syntheticLocationData && (
              <span className="block text-muted-foreground">
                Synthetic coordinates
              </span>
            )}
            {popup.topFactors && popup.topFactors.length > 0 && (
              <span className="block text-muted-foreground">
                Top factors: {popup.topFactors.join(", ")}
              </span>
            )}
          </div>
        </Popup>
      )}
    </Map>
  );
}