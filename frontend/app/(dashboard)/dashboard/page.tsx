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
import {
  dashboardKPIs,
  predictedLocations,
  recentAlerts,
} from "@/mocks/dashboard";
import { gisLocations } from "@/mocks/gis";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeading
        title="Dashboard"
        description="Real-time overview of cybercrime cases and predictive intelligence"
      >
        <span>Last Updated: 15 Sep 2026, 11:24 AM</span>
        <button
          type="button"
          className="flex size-8 items-center justify-center rounded-md border border-border bg-card text-muted-foreground"
        >
          <RefreshCw className="size-4" />
        </button>
        <select className="rounded-md border border-border bg-card px-2 py-1.5 text-xs">
          <option>Last 7 Days</option>
          <option>Last 24 Hours</option>
          <option>Last 30 Days</option>
        </select>
      </PageHeading>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={FileText}
          tone="blue"
          value={dashboardKPIs.totalCases.toLocaleString("en-IN")}
          label="Total Cases"
          note="▲ 12% from last month"
        />
        <StatCard
          icon={AlertTriangle}
          tone="red"
          value={String(dashboardKPIs.highRiskCases)}
          label="High Risk Cases"
          note="▲ 5% from last week"
        />
        <StatCard
          icon={Bell}
          tone="orange"
          value={String(dashboardKPIs.activeAlerts)}
          label="Active Alerts"
          note="▲ 23 unacknowledged"
        />
        <StatCard
          icon={BarChart3}
          tone="green"
          value={String(dashboardKPIs.predictionsToday)}
          label="Predictions Today"
          note="Across 14 districts"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Panel
          icon={Map}
          title="Cybercrime Risk Map (Last 7 Days)"
          actions={
            <div className="flex items-center gap-3 text-xs">
              <label className="flex items-center gap-2">
                Region
                <select className="rounded-md border border-border bg-card px-2 py-1">
                  <option>Pune</option>
                  <option>Mumbai</option>
                  <option>Delhi</option>
                </select>
              </label>
              <label className="flex items-center gap-2">
                Crime Type
                <select className="rounded-md border border-border bg-card px-2 py-1">
                  <option>All</option>
                  <option>Financial Fraud</option>
                  <option>UPI Fraud</option>
                </select>
              </label>
              <button
                type="button"
                className="flex size-8 items-center justify-center rounded-md border border-border text-muted-foreground"
              >
                <Map className="size-4" />
              </button>
            </div>
          }
        >
          <div className="h-80 w-full rounded-b-lg p-2">
            <RiskMap locations={gisLocations} />
          </div>
        </Panel>

        <Panel
          icon={MapPin}
          title="Top Predicted Locations (Next 24 Hours)"
          actions={
            <Link
              href="/predictions"
              className="flex items-center gap-1 text-xs font-medium text-primary"
            >
              View All <ArrowRight className="size-3.5" />
            </Link>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                  <th className="px-5 py-3">#</th>
                  <th className="px-5 py-3">Location / Area</th>
                  <th className="px-5 py-3">District</th>
                  <th className="px-5 py-3">Risk Score</th>
                  <th className="px-5 py-3">Confidence</th>
                  <th className="px-5 py-3">Prediction Window</th>
                </tr>
              </thead>
              <tbody>
                {predictedLocations.map((location) => (
                  <tr
                    key={location.number}
                    className="border-b border-border last:border-0 hover:bg-muted/50"
                  >
                    <td className="px-5 py-3">{location.number}</td>
                    <td className="px-5 py-3 font-medium">{location.location}</td>
                    <td className="px-5 py-3">{location.district}</td>
                    <td className="px-5 py-3">
                      <ScoreChip score={location.score} level={location.risk} />
                    </td>
                    <td className="px-5 py-3">
                      <ConfidenceChip level={location.confidence} />
                    </td>
                    <td className="px-5 py-3">{location.window}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
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
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                  <th className="px-5 py-3">Time</th>
                  <th className="px-5 py-3">Case ID</th>
                  <th className="px-5 py-3">Location</th>
                  <th className="px-5 py-3">Alert Type</th>
                  <th className="px-5 py-3">Severity</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Assigned To</th>
                </tr>
              </thead>
              <tbody>
                {recentAlerts.map((alert) => (
                  <tr
                    key={alert.caseId}
                    className="border-b border-border last:border-0 hover:bg-muted/50"
                  >
                    <td className="px-5 py-3">{alert.time}</td>
                    <td className="px-5 py-3">
                      <Link
                        href={`/cases/${alert.caseId}`}
                        className="font-semibold text-primary"
                      >
                        {alert.caseId}
                      </Link>
                    </td>
                    <td className="px-5 py-3">{alert.location}</td>
                    <td className="px-5 py-3">{alert.type}</td>
                    <td className="px-5 py-3">
                      <SeverityBadge level={alert.severity} />
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge status={alert.status} />
                    </td>
                    <td className="px-5 py-3">{alert.assigned}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

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
                href: "/predictions",
                icon: BarChart3,
                title: "Run Prediction",
                note: "Generate location predictions",
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

          <div className="mx-5 mb-5 flex items-start gap-3 rounded-lg border border-border bg-muted/50 p-4">
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
        </Panel>
      </div>
    </div>
  );
}