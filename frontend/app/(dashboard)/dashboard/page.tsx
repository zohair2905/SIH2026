"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Bell,
  FilePlus,
  FileText,
  Info,
  Map,
  MapPin,
  RefreshCw,
  Zap,
} from "lucide-react";

import { PageHeading } from "@/components/layout/page-heading";
import { SeverityBadge, StatusBadge } from "@/components/badges/";
import { RiskMap } from "@/components/gis/risk-map";
import { StatCard } from "@/components/ui/stat-card";
import { ConfidenceChip, ScoreChip } from "@/components/ui/score-chip";
import { Panel } from "@/components/ui/panel";
import { getDashboard } from "@/lib/api/dashboard";
import type {
  AlertRecord,
  DashboardOverview,
  DashboardTopAtm,
  GisLocation,
} from "@/types";

const severityOrder = ["critical", "high", "medium", "low"] as const;
const severityColors: Record<(typeof severityOrder)[number], string> = {
  critical: "#8a1f1f",
  high: "#dc4545",
  medium: "#f39a18",
  low: "#21965f",
};

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString("en-IN");
}

function toGisLocation(atm: DashboardTopAtm): GisLocation {
  return {
    name: atm.atm_id,
    area: atm.area_type ?? atm.atm_id,
    score: Math.round(atm.risk_score * 100),
    risk: atm.severity,
    cases: atm.observation_count,
    window: "Next 24 Hours",
    position: [atm.latitude, atm.longitude],
    confidence: atm.confidence,
    syntheticLocationData: atm.synthetic_location_data,
  };
}

function SeverityList({
  title,
  counts,
}: {
  title: string;
  counts: Record<(typeof severityOrder)[number], number>;
}) {
  return (
    <div className="p-5">
      <strong className="block text-sm text-foreground">{title}</strong>
      <ul className="mt-3 space-y-2">
        {severityOrder.map((level) => (
          <li
            key={level}
            className="flex items-center justify-between text-sm"
          >
            <span className="flex items-center gap-2 text-muted-foreground">
              <span
                className="size-2.5 rounded-full"
                style={{ backgroundColor: severityColors[level] }}
              />
              {level.charAt(0).toUpperCase() + level.slice(1)}
            </span>
            <strong className="text-foreground">{counts[level]}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);

  const load = useCallback(() => {
    getDashboard().then((result) => {
      setData(result.data);
      setOffline(result.mocked);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const refresh = () => {
    setLoading(true);
    void load();
  };

  const summary = data?.summary ?? null;
  const kpis =
    summary && data
      ? [
          {
            value: String(summary.cases),
            note:
              summary.predictions > 0
                ? `${summary.predictions} current-run predictions`
                : "Registered complaints",
          },
          {
            value:
              summary.average_prediction_risk !== null
                ? `${Math.round(summary.average_prediction_risk * 100)}%`
                : "—",
            note: "Mean current-run risk score",
          },
          {
            value: String(summary.active_alerts),
            note:
              summary.unacknowledged_alerts > 0
                ? `${summary.unacknowledged_alerts} unacknowledged`
                : "Active (new + acknowledged)",
          },
          {
            value: String(summary.open_cases),
            note: `${summary.cases} total cases`,
          },
        ]
      : null;

  const mapLocations = (data?.top_atms ?? [])
    .slice(0, 10)
    .map(toGisLocation);

  return (
    <div className="space-y-6">
      <PageHeading
        title="Dashboard"
        description="Real-time overview of cybercrime cases and predictive intelligence"
      >
        <span>{loading ? "Loading…" : "Live data from backend"}</span>
        <button
          type="button"
          onClick={refresh}
          className="flex size-8 items-center justify-center rounded-md border border-border bg-card text-muted-foreground"
          aria-label="Refresh dashboard"
        >
          <RefreshCw className="size-4" />
        </button>
      </PageHeading>

      {offline && (
        <p className="rounded-md border border-border bg-muted/40 px-4 py-2 text-xs text-muted-foreground">
          Backend unreachable — dashboard data is unavailable.
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={FileText}
          tone="blue"
          value={loading ? "…" : (kpis?.[0].value ?? "—")}
          label="Total Cases"
          note={kpis?.[0].note ?? ""}
        />
        <StatCard
          icon={BarChart3}
          tone="green"
          value={loading ? "…" : (kpis?.[1].value ?? "—")}
          label="Average Current Risk"
          note={kpis?.[1].note ?? ""}
        />
        <StatCard
          icon={Bell}
          tone="orange"
          value={loading ? "…" : (kpis?.[2].value ?? "—")}
          label="Active Alerts"
          note={kpis?.[2].note ?? ""}
        />
        <StatCard
          icon={AlertTriangle}
          tone="red"
          value={loading ? "…" : (kpis?.[3].value ?? "—")}
          label="Open Cases"
          note={kpis?.[3].note ?? ""}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Panel
          icon={Map}
          title="Cybercrime Risk Map"
          subtitle="Top predicted ATMs from current prediction runs"
          className="xl:col-span-2"
        >
          <div className="h-80 w-full rounded-b-lg p-2">
            {loading ? (
              <div className="flex size-full items-center justify-center text-sm text-muted-foreground">
                Loading risk map…
              </div>
            ) : mapLocations.length === 0 ? (
              <div className="flex size-full items-center justify-center text-sm text-muted-foreground">
                No predicted locations for the current runs.
              </div>
            ) : (
              <RiskMap locations={mapLocations} />
            )}
          </div>
        </Panel>

        <Panel icon={MapPin} title="Risk Overview" subtitle="Current distribution">
          <div className="grid gap-4 lg:grid-cols-1">
            {data ? (
              <>
                <SeverityList
                  title="Cases (current-run top risk)"
                  counts={data.case_risk_distribution}
                />
                <SeverityList
                  title="Alerts (all severity)"
                  counts={data.alert_severity_distribution}
                />
              </>
            ) : (
              <p className="p-5 text-sm text-muted-foreground">
                No distribution data available.
              </p>
            )}
          </div>
        </Panel>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Panel
          icon={MapPin}
          title="Top Predicted Locations (Next 24 Hours)"
          actions={
            <Link
              href="/gis"
              className="flex items-center gap-1 text-xs font-medium text-primary"
            >
              View on GIS <ArrowRight className="size-3.5" />
            </Link>
          }
        >
          <div className="overflow-x-auto">
            {loading ? (
              <div className="px-5 py-10 text-center text-sm text-muted-foreground">
                Loading predicted locations…
              </div>
            ) : !data || data.top_atms.length === 0 ? (
              <div className="px-5 py-10 text-center text-sm text-muted-foreground">
                No current-run predictions to display.
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                    <th className="px-5 py-3">#</th>
                    <th className="px-5 py-3">ATM / Area</th>
                    <th className="px-5 py-3">Risk Score</th>
                    <th className="px-5 py-3">Severity</th>
                    <th className="px-5 py-3">Confidence</th>
                    <th className="px-5 py-3">Window</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_atms.map((atm, index) => (
                    <tr
                      key={atm.atm_id}
                      className="border-b border-border last:border-0 hover:bg-muted/50"
                    >
                      <td className="px-5 py-3">{index + 1}</td>
                      <td className="px-5 py-3 font-medium">
                        {atm.atm_id}
                        {atm.area_type ? (
                          <span className="block text-xs text-muted-foreground">
                            {atm.area_type}
                          </span>
                        ) : null}
                      </td>
                      <td className="px-5 py-3">
                        <ScoreChip
                          score={`${Math.round(atm.risk_score * 100)}%`}
                          level={atm.severity}
                        />
                      </td>
                      <td className="px-5 py-3">
                        <SeverityBadge level={atm.severity} />
                      </td>
                      <td className="px-5 py-3">
                        <ConfidenceChip
                          level={
                            atm.confidence >= 0.7
                              ? "high"
                              : atm.confidence >= 0.4
                                ? "medium"
                                : "low"
                          }
                        />
                      </td>
                      <td className="px-5 py-3">Next 24 Hours</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Panel>

        <Panel
          icon={Bell}
          title="Recent Alerts"
          actions={
            <Link
              href="/alerts"
              className="flex items-center gap-1 text-xs font-medium text-primary"
            >
              View All <ArrowRight className="size-3.5" />
            </Link>
          }
        >
          <div className="overflow-x-auto">
            {loading ? (
              <div className="px-5 py-10 text-center text-sm text-muted-foreground">
                Loading alerts…
              </div>
            ) : !data || data.recent_alerts.length === 0 ? (
              <div className="px-5 py-10 text-center text-sm text-muted-foreground">
                No alerts yet.
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                    <th className="px-5 py-3">Time</th>
                    <th className="px-5 py-3">Case ID</th>
                    <th className="px-5 py-3">ATM / Message</th>
                    <th className="px-5 py-3">Severity</th>
                    <th className="px-5 py-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_alerts.map((alert: AlertRecord) => (
                    <tr
                      key={alert.alert_id}
                      className="border-b border-border last:border-0 hover:bg-muted/50"
                    >
                      <td className="px-5 py-3 whitespace-nowrap">
                        {formatDateTime(alert.created_at)}
                      </td>
                      <td className="px-5 py-3">
                        <Link
                          href={`/cases/${alert.case_id}`}
                          className="font-semibold text-primary"
                        >
                          {alert.case_id}
                        </Link>
                      </td>
                      <td className="max-w-56 px-5 py-3">
                        <span className="block truncate font-medium">
                          {alert.atm_id}
                        </span>
                        <span className="block truncate text-xs text-muted-foreground">
                          {alert.message}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <SeverityBadge level={alert.severity} />
                      </td>
                      <td className="px-5 py-3">
                        <StatusBadge status={alert.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Panel>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Panel icon={Zap} title="Quick Actions">
          <div className="grid gap-3 p-5 sm:grid-cols-2">
            {[
              {
                href: "/cases",
                icon: FilePlus,
                title: "Register New Case",
                note: "Add a new complaint / case",
              },
              {
                href: "/gis",
                icon: Map,
                title: "View GIS Map",
                note: "Explore risk locations",
              },
              {
                href: "/alerts",
                icon: Bell,
                title: "Review Alerts",
                note: "Acknowledge and resolve alerts",
              },
              {
                href: "/reports",
                icon: FileText,
                title: "Generate Report",
                note: "Create investigative report",
              },
            ].map(({ href, icon: Icon, title, note }) => (
              <Link
                key={href}
                href={href}
                className="flex items-center gap-3 rounded-lg border border-border p-3 transition-colors hover:bg-muted/50"
              >
                <div className="flex size-10 shrink-0 items-center justify-center rounded-md bg-accent text-primary">
                  <Icon className="size-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <strong className="block text-sm">{title}</strong>
                  <span className="block text-xs text-muted-foreground">
                    {note}
                  </span>
                </div>
                <ArrowRight className="size-4 shrink-0 text-muted-foreground" />
              </Link>
            ))}
          </div>
        </Panel>

        <div className="flex items-start gap-3 rounded-lg border border-border bg-secondary px-5 py-4">
          <Info className="mt-0.5 size-5 shrink-0 text-primary" />
          <p className="text-xs leading-relaxed text-muted-foreground">
            This platform provides predictive risk estimates to support
            investigations. Predictions are decision-support tools and not
            proof of criminal activity.
          </p>
          <Link
            href="/predictions"
            className="flex shrink-0 items-center gap-1 text-xs font-medium text-primary"
          >
            Learn More <ArrowRight className="size-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}