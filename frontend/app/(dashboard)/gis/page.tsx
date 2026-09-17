import { LayoutDashboard as Dashboard, MapPin } from "lucide-react";

import { PageHeading } from "@/components/layout/page-heading";
import { RiskMap } from "@/components/gis/risk-map";
import { Panel } from "@/components/ui/panel";
import { gisLocations } from "@/mocks/gis";
import type { GisLocation, SeverityLevel } from "@/types";

const riskColors: Record<SeverityLevel, string> = {
  high: "#dc4545",
  medium: "#f39a18",
  low: "#21965f",
};

const riskLabels: Record<SeverityLevel, string> = {
  high: "High Risk",
  medium: "Medium Risk",
  low: "Low Risk",
};

const zoneSummary = {
  total: gisLocations.length,
  high: gisLocations.filter((l) => l.risk === "high").length,
  medium: gisLocations.filter((l) => l.risk === "medium").length,
  low: gisLocations.filter((l) => l.risk === "low").length,
  cases: gisLocations.reduce((sum, l) => sum + l.cases, 0),
};

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
  const sortedLocations = [...gisLocations].sort((a, b) => b.score - a.score);

  return (
    <div className="space-y-6">
      <PageHeading
        title="GIS Intelligence"
        description="Geospatial risk mapping for proactive cybercrime prevention"
      >
        <span>Map data last updated: 16 Sep 2026, 14:30</span>
      </PageHeading>

      <div className="flex flex-wrap items-center gap-5 rounded-lg border border-border bg-card p-4">
        {[
          ["Coverage Area", "Pune City"],
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
            <RiskMap locations={gisLocations} />
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
            {sortedLocations.map((location) => (
              <LocationRow key={location.name} location={location} />
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}