import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  Clock,
  FileSearch,
  FileText,
  IndianRupee,
  Map,
  MapPin,
  TrendingUp,
  User,
} from "lucide-react";

import { SeverityBadge, StatusBadge } from "@/components/badges";
import { Panel } from "@/components/ui/panel";
import { initialCases } from "@/mocks/cases";

const timelineEvents = [
  {
    icon: CheckCircle,
    title: "Complaint Registered",
    time: "15 Sep 2026 • 08:32 AM",
  },
  {
    icon: Activity,
    title: "Risk Analysis Completed",
    time: "15 Sep 2026 • 09:05 AM",
  },
  {
    icon: TrendingUp,
    title: "Prediction Generated",
    time: "15 Sep 2026 • 09:18 AM",
  },
  {
    icon: AlertTriangle,
    title: "High Risk Alert Created",
    time: "15 Sep 2026 • 09:20 AM",
  },
];

const evidenceItems = [
  { name: "Complaint Report", meta: "PDF • 245 KB" },
  { name: "Transaction Summary", meta: "PDF • 128 KB" },
  { name: "Risk Analysis Report", meta: "PDF • 310 KB" },
];

const riskFactors: { label: string; level: "high" | "medium" }[] = [
  { label: "Transaction Pattern", level: "high" },
  { label: "Location Risk", level: "high" },
  { label: "Account Linkage", level: "medium" },
  { label: "Historical Similarity", level: "high" },
];

export default async function CaseDetailsPage({
  params,
}: PageProps<"/cases/[id]">) {
  const { id } = await params;

  const fallback = initialCases.find((c) => c.id === "CC-2026-4381")!;
  const match = initialCases.find((c) => c.id === id) ?? {
    ...fallback,
    id,
  };

  const details = [
    ["Case ID", match.id],
    ["Complaint Type", match.type],
    ["Registration Date", match.date],
    ["Current Status", "New"],
    ["Transaction Channel", "UPI"],
    ["Reported Location", match.location],
    ["Financial Institution", "Demo National Bank"],
    ["Complaint Source", "Cyber Crime Portal"],
  ];

  return (
    <div className="space-y-6">
      <Link
        href="/cases"
        className="flex w-fit items-center gap-2 text-sm font-medium text-primary"
      >
        <ArrowLeft className="size-4" /> Back to Cases
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold text-foreground">
              Case {match.id}
            </h1>
            <SeverityBadge level={match.risk} />
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {match.type} • Registered on {match.date}
          </p>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium"
          >
            Assign Officer
          </button>
          <button
            type="button"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white"
          >
            Update Case
          </button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { icon: MapPin, label: "Location", value: match.location },
          { icon: IndianRupee, label: "Amount Involved", value: match.amount },
          { icon: Activity, label: "Risk Score", value: match.score },
          { icon: User, label: "Assigned Officer", value: match.officer },
        ].map(({ icon: Icon, label, value }) => (
          <div
            key={label}
            className="flex items-center gap-4 rounded-lg border border-border bg-card p-5 shadow-sm"
          >
            <div className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-accent text-primary">
              <Icon className="size-5" />
            </div>
            <div className="min-w-0">
              <span className="block text-xs text-muted-foreground">
                {label}
              </span>
              <strong className="block truncate text-sm text-foreground">
                {value}
              </strong>
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Panel icon={FileText} title="Case Information">
            <div className="grid gap-x-6 gap-y-4 p-5 sm:grid-cols-2">
              {details.map(([label, value]) => (
                <div key={label}>
                  <span className="block text-xs text-muted-foreground">
                    {label}
                  </span>
                  {label === "Current Status" ? (
                    <StatusBadge status={match.status} className="mt-1" />
                  ) : (
                    <strong className="mt-1 block text-sm text-foreground">
                      {value}
                    </strong>
                  )}
                </div>
              ))}
            </div>
          </Panel>

          <Panel
            icon={TrendingUp}
            title="Predictive Intelligence"
            actions={
              <Link
                href="/predictions"
                className="text-xs font-medium text-primary"
              >
                View Prediction
              </Link>
            }
          >
            <div className="p-5">
              <div className="flex items-start gap-5 rounded-lg border border-border bg-muted/40 p-5">
                <div className="flex size-24 shrink-0 items-center justify-center rounded-full border-8 border-risk text-2xl font-bold text-risk">
                  {match.score}
                </div>
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Predicted Withdrawal Risk
                  </span>
                  <h3 className="mt-1 text-lg font-semibold text-foreground">
                    High probability of withdrawal activity
                  </h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    The predictive model identifies a high-risk withdrawal
                    window based on historical transaction patterns and
                    location signals.
                  </p>
                </div>
              </div>

              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                {[
                  { icon: Clock, label: "Predicted Window", value: "14:00 – 18:00" },
                  { icon: MapPin, label: "Predicted Area", value: "Hadapsar ATM Cluster" },
                  { icon: Activity, label: "Model Confidence", value: "High" },
                ].map(({ icon: Icon, label, value }) => (
                  <div
                    key={label}
                    className="flex items-center gap-3 rounded-lg border border-border p-3"
                  >
                    <Icon className="size-5 shrink-0 text-primary" />
                    <div className="min-w-0">
                      <span className="block text-xs text-muted-foreground">
                        {label}
                      </span>
                      <strong className="block truncate text-sm text-foreground">
                        {value}
                      </strong>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Panel>

          <Panel icon={Clock} title="Case Timeline">
            <div className="p-5">
              {timelineEvents.map(({ icon: Icon, title, time }, index) => (
                <div key={title} className="relative flex gap-4 pb-5 last:pb-0">
                  {index < timelineEvents.length - 1 && (
                    <span className="absolute left-4 top-9 h-full w-px bg-border" />
                  )}
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-accent text-primary">
                    <Icon className="size-4" />
                  </div>
                  <div>
                    <strong className="block text-sm text-foreground">
                      {title}
                    </strong>
                    <span className="text-xs text-muted-foreground">
                      {time}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel icon={AlertTriangle} title="Risk Assessment">
            <div className="p-5">
              <div className="flex items-end justify-center py-4">
                <div className="text-center">
                  <strong className="block text-5xl font-bold text-risk">
                    {match.score}
                  </strong>
                  <span className="text-sm text-muted-foreground">
                    Overall Risk
                  </span>
                </div>
              </div>

              <div className="mb-5 h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-risk"
                  style={{ width: match.score }}
                />
              </div>

              <div className="space-y-3">
                {riskFactors.map(({ label, level }) => (
                  <div
                    key={label}
                    className="flex items-center justify-between"
                  >
                    <span className="text-sm text-muted-foreground">
                      {label}
                    </span>
                    <span
                      className={
                        level === "high"
                          ? "font-semibold text-risk"
                          : "font-semibold text-risk-med"
                      }
                    >
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </Panel>

          <Panel icon={Map} title="Predicted Withdrawal">
            <div className="p-5">
              <div className="mb-4 flex items-center gap-4 rounded-lg border border-border bg-muted/40 p-4">
                <MapPin className="size-6 shrink-0 text-primary" />
                <div>
                  <strong className="block text-sm text-foreground">
                    Hadapsar ATM Cluster
                  </strong>
                  <span className="text-xs text-muted-foreground">
                    Pune, Maharashtra
                  </span>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                {[
                  ["Prediction Window", "14:00 – 18:00"],
                  ["Risk Score", match.score],
                  ["Nearby Cases", "17"],
                ].map(([label, value]) => (
                  <div key={label}>
                    <span className="block text-xs text-muted-foreground">
                      {label}
                    </span>
                    <strong className="mt-1 block text-sm text-foreground">
                      {value}
                    </strong>
                  </div>
                ))}
              </div>

              <Link
                href="/gis"
                className="mt-5 flex w-fit items-center gap-2 rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-primary"
              >
                <Map className="size-4" /> View on GIS Map
              </Link>
            </div>
          </Panel>

          <Panel icon={FileSearch} title="Evidence & Documents">
            <div className="p-5">
              {evidenceItems.map(({ name, meta }) => (
                <div
                  key={name}
                  className="flex items-center gap-3 rounded-lg border border-border p-3 last:mt-3"
                >
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-accent text-primary">
                    <FileText className="size-4" />
                  </div>
                  <div>
                    <strong className="block text-sm text-foreground">
                      {name}
                    </strong>
                    <span className="text-xs text-muted-foreground">
                      {meta}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}