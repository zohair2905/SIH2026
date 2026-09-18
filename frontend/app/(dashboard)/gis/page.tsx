"use client";

import { useEffect, useState } from "react";
import { LayoutDashboard as Dashboard, MapPin } from "lucide-react";

import { PageHeading } from "@/components/layout/page-heading";
import { RiskMap } from "@/components/gis/risk-map";
import { Panel } from "@/components/ui/panel";
import { getHeatmap } from "@/lib/api/heatmap";
import type { GisLocation, HeatmapPoint, SeverityLevel } from "@/types";

const riskColors: Record<SeverityLevel, string> = {
  critical: "#8a1f1f",
  high: "#dc4545",
  medium: "#f39a18",
  low: "#21965f",
};

const riskLabels: Record<SeverityLevel, string> = {
  critical: "Critical Risk",
  high: "High Risk",
  medium: "Medium Risk",
  low: "Low Risk",
};

const timeFormat = new Intl.DateTimeFormat("en-GB", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

function formatWindow(point: HeatmapPoint): string {
  if (!point.window_start || !point.window_end) return "Next 24 Hours";
  const start = new Date(point.window_start);
  const end = new Date(point.window_end);
  const valid =
    !Number.isNaN(start.getTime()) && !Number.isNaN(end.getTime());
  if (!valid) return "Next 24 Hours";
  return `${timeFormat.format(start)} – ${timeFormat.format(end)}`;
}

function toGisLocation(point: HeatmapPoint): GisLocation {
  return {
    name: point.atm_id,
    area: point.area_type ?? point.atm_id,
    score: Math.round(point.risk_score * 100),
    risk: point.severity,
    cases: point.observation_count,
    window: formatWindow(point),
    position: [point.latitude, point.longitude],
    confidence: point.confidence,
    topFactors: point.top_factors.map((factor) => factor.label),
    syntheticLocationData: point.synthetic_location_data,
  };
}

function LegendDot({ risk }: { risk: SeverityLevel }) {
  return (
    <span
      className="mr-1.5 inline-block size-2.5 rounded-full"
      style={{ backgroundColor: riskColors[risk] }}
    />
  );
}

function LocationRow({ location }: { location: GisLocation }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border py-2.5 last:border-0">
      <div className="flex items-center gap-2">
        <span
          className="inline-block size-2.5 rounded-full"
          style={{ backgroundColor: riskColors[location.risk] }}
        />
        <div>
          <span className="block text-sm font-medium text-foreground">
            {location.name}
          </span>
          <small className="block text-xs text-muted-foreground">
            {location.area} • {location.cases} cases
          </small>
        </div>
      </div>
      <div className="text-right">
        <strong className="block text-sm text-foreground">
          {location.score}%
        </strong>
        <small className="block text-xs text-muted-foreground">
          {location.window}
        </small>
      </div>
    </div>
  );
}

export default function GisPage() {
  const [locations, setLocations] = useState<GisLocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [mocked, setMocked] = useState(false);

  useEffect(() => {
    let active = true;
    getHeatmap().then((result) => {
      if (!active) return;
      setMocked(result.mocked);
      setLocations(result.data.points.map(toGisLocation));
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, []);

  const sortedLocations = [...locations].sort((a, b) => b.score - a.score);

  const zoneSummary = {
    total: locations.length,
    critical: locations.filter((l) => l.risk === "critical").length,
    high: locations.filter((l) => l.risk === "high").length,
    medium: locations.filter((l) => l.risk === "medium").length,
    low: locations.filter((l) => l.risk === "low").length,
    cases: locations.reduce((sum, l) => sum + l.cases, 0),
  };

  return (
    <div className="space-y-6">
      <PageHeading
        title="GIS Intelligence"
        description="Geospatial risk mapping for proactive cybercrime prevention"
      >
        {mocked && (
          <span className="text-muted-foreground">
            Showing offline sample data
          </span>
        )}
        {!mocked && !loading && (
          <span>Map data from live prediction runs</span>
        )}
      </PageHeading>

      <div className="flex flex-wrap items-center gap-5 rounded-lg border border-border bg-card p-4">
        {[
          ["Coverage Area", "Pune City"],
          ["Critical Risk Zones", zoneSummary.critical],
          ["High Risk Zones", zoneSummary.high],
          ["Medium Risk Zones", zoneSummary.medium],
          ["Low Risk Zones", zoneSummary.low],
          ["Total Vulnerable Points", zoneSummary.cases],
          ["Prediction Window", "Next 24 Hours"],
        ].map(([label, value]) => (
          <div key={label}>
            <small className="block text-xs text-muted-foreground">
              {label}
            </small>
            <strong className="block text-base text-foreground">
              {value}
            </strong>
          </div>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Panel
          icon={MapPin}
          title="Risk Heatmap"
          subtitle="Predicted cybercrime hotspots in Pune City"
          className="xl:col-span-2"
        >
          <div className="h-[480px] w-full rounded-md p-2">
            {loading ? (
              <div className="flex size-full items-center justify-center text-sm text-muted-foreground">
                Loading risk zones…
              </div>
            ) : locations.length === 0 ? (
              <div className="flex size-full items-center justify-center text-sm text-muted-foreground">
                No risk zones found for the current prediction run.
              </div>
            ) : (
              <RiskMap locations={locations} />
            )}
          </div>
          <div className="flex flex-wrap items-center gap-4 px-2 pt-2 text-xs text-muted-foreground">
            {(Object.keys(riskLabels) as SeverityLevel[]).map((risk) => (
              <span key={risk} className="flex items-center">
                <LegendDot risk={risk} /> {riskLabels[risk]}
              </span>
            ))}
          </div>
        </Panel>

        <Panel icon={Dashboard} title="Risk Locations" subtitle="Ranked by prediction score">
          <div className="p-3">
            {loading ? (
              <div className="py-10 text-center text-sm text-muted-foreground">
                Loading risk locations…
              </div>
            ) : locations.length === 0 ? (
              <div className="py-10 text-center text-sm text-muted-foreground">
                No risk locations found.
              </div>
            ) : (
              sortedLocations.map((location) => (
                <LocationRow key={location.name} location={location} />
              ))
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}