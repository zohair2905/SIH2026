"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Bell,
  CheckCircle,
  Clock,
  Eye,
  Filter,
  RefreshCw,
  Search,
} from "lucide-react";
import { toast } from "sonner";

import { PageHeading } from "@/components/layout/page-heading";
import { SeverityBadge, StatusBadge } from "@/components/badges";
import { Panel } from "@/components/ui/panel";
import { StatCard } from "@/components/ui/stat-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { acknowledgeAlert, getAlerts, resolveAlert } from "@/lib/api/alerts";
import type { AlertRecord, AlertStatus } from "@/types";

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString("en-IN");
}

function riskPercent(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [selectedAlert, setSelectedAlert] = useState<AlertRecord | null>(null);

  const load = useCallback(() => {
    getAlerts().then((result) => {
      setAlerts(result.data);
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

  const replaceAlert = (updated: AlertRecord | null, id: number) => {
    if (updated === null) {
      toast.error("Backend did not confirm the alert update.");
      return;
    }
    setAlerts((previous) =>
      previous.map((alert) => (alert.alert_id === id ? updated : alert))
    );
    setSelectedAlert((previous) =>
      previous && previous.alert_id === id ? updated : previous
    );
    toast.success(`Alert ${id} is now ${updated.status}.`);
  };

  const handleAcknowledge = async (id: number) => {
    replaceAlert(await acknowledgeAlert(id), id);
  };

  const handleResolve = async (id: number) => {
    replaceAlert(await resolveAlert(id), id);
  };

  const filteredAlerts = alerts.filter((alert) => {
    const matchesSearch =
      String(alert.alert_id).toLowerCase().includes(search.toLowerCase()) ||
      alert.case_id.toLowerCase().includes(search.toLowerCase()) ||
      alert.atm_id.toLowerCase().includes(search.toLowerCase()) ||
      alert.message.toLowerCase().includes(search.toLowerCase());

    const matchesSeverity =
      severityFilter === "All" || alert.severity === severityFilter.toLowerCase();

    const matchesStatus =
      statusFilter === "All" || alert.status === statusFilter.toLowerCase();

    return matchesSearch && matchesSeverity && matchesStatus;
  });

  const activeCount = alerts.filter((a) =>
    ["new", "acknowledged"].includes(a.status)
  ).length;
  const highSeverityCount = alerts.filter(
    (a) => a.severity === "high" || a.severity === "critical"
  ).length;
  const unacknowledgedCount = alerts.filter((a) => a.status === "new").length;
  const resolvedCount = alerts.filter((a) => a.status === "resolved").length;

  const isOpen = (status: AlertStatus) => status === "new";
  const isAcknowledged = (status: AlertStatus) => status === "acknowledged";

  return (
    <div className="space-y-6">
      <PageHeading
        title="Alert Management"
        description="Monitor and respond to real-time cybercrime intelligence alerts"
      >
        <span>{loading ? "Loading…" : `${alerts.length} alerts loaded`}</span>
        <button
          type="button"
          onClick={refresh}
          className="flex size-8 items-center justify-center rounded-md border border-border bg-card text-muted-foreground"
          aria-label="Refresh alerts"
        >
          <RefreshCw className="size-4" />
        </button>
      </PageHeading>

      {offline && (
        <p className="rounded-md border border-border bg-muted/40 px-4 py-2 text-xs text-muted-foreground">
          Backend unreachable — no alerts to display.
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={Bell}
          tone="blue"
          value={String(activeCount)}
          label="Active Alerts"
          note="New + acknowledged"
        />
        <StatCard
          icon={AlertTriangle}
          tone="red"
          value={String(highSeverityCount)}
          label="High Severity"
          note="Immediate attention"
        />
        <StatCard
          icon={Clock}
          tone="orange"
          value={String(unacknowledgedCount)}
          label="Unacknowledged"
          note="Awaiting officer action"
        />
        <StatCard
          icon={CheckCircle}
          tone="green"
          value={String(resolvedCount)}
          label="Resolved"
          note="Alerts closed"
        />
      </div>

      <Panel
        icon={Bell}
        title="Intelligence Alerts"
        subtitle="Alerts generated by the predictive engine from persisted prediction runs"
      >
        <div className="flex flex-wrap items-center gap-3 border-b border-border px-5 py-4">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="w-64 pl-9"
              placeholder="Search alert, case, ATM or message..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="relative">
            <Filter className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <select
              className="h-9 rounded-md border border-input bg-background pl-9 pr-3 text-sm"
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
            >
              <option value="All">All Severity</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="All">All Status</option>
            <option value="new">New</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="dismissed">Dismissed</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                <th className="px-5 py-3">Alert ID</th>
                <th className="px-5 py-3">Time</th>
                <th className="px-5 py-3">ATM / Message</th>
                <th className="px-5 py-3">Risk Score</th>
                <th className="px-5 py-3">Severity</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Case</th>
                <th className="px-5 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td
                    colSpan={8}
                    className="px-5 py-10 text-center text-sm text-muted-foreground"
                  >
                    Loading alerts…
                  </td>
                </tr>
              )}

              {!loading &&
                filteredAlerts.map((alert) => (
                  <tr
                    key={alert.alert_id}
                    className="border-b border-border last:border-0 hover:bg-muted/50"
                  >
                    <td className="px-5 py-3 font-semibold text-primary">
                      {alert.alert_id}
                    </td>
                    <td className="px-5 py-3 whitespace-nowrap">
                      {formatDateTime(alert.created_at)}
                    </td>
                    <td className="max-w-64 px-5 py-3">
                      <span className="block truncate font-medium">
                        {alert.atm_id}
                      </span>
                      <span className="block truncate text-xs text-muted-foreground">
                        {alert.message}
                      </span>
                    </td>
                    <td className="px-5 py-3 font-medium">
                      {riskPercent(alert.risk_score)}
                    </td>
                    <td className="px-5 py-3">
                      <SeverityBadge level={alert.severity} />
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge status={alert.status} />
                    </td>
                    <td className="px-5 py-3">
                      <Link
                        href={`/cases/${alert.case_id}`}
                        className="font-semibold text-primary"
                      >
                        {alert.case_id}
                      </Link>
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setSelectedAlert(alert)}
                        >
                          <Eye className="size-3.5" /> View
                        </Button>
                        {isOpen(alert.status) && (
                          <Button
                            size="sm"
                            onClick={() => void handleAcknowledge(alert.alert_id)}
                          >
                            Acknowledge
                          </Button>
                        )}
                        {isAcknowledged(alert.status) && (
                          <Button
                            size="sm"
                            className="bg-green-700 hover:bg-green-800"
                            onClick={() => void handleResolve(alert.alert_id)}
                          >
                            Resolve
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>

          {!loading && filteredAlerts.length === 0 && (
            <div className="py-10 text-center text-sm text-muted-foreground">
              {alerts.length === 0
                ? "No alerts have been generated yet."
                : "No alerts found matching your filters."}
            </div>
          )}
        </div>
      </Panel>

      <div className="flex items-start gap-3 rounded-lg border border-border bg-secondary p-4">
        <AlertTriangle className="mt-0.5 size-4 shrink-0 text-primary" />
        <div>
          <strong className="block text-sm text-foreground">
            Intelligence Alert Notice
          </strong>
          <span className="text-xs leading-relaxed text-muted-foreground">
            Alerts shown here are generated from predictive analytics and
            should be verified by authorized personnel before operational
            action.
          </span>
        </div>
      </div>

      <Dialog
        open={selectedAlert !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedAlert(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Alert {selectedAlert?.alert_id}</DialogTitle>
            <DialogDescription>
              {selectedAlert
                ? `Prediction-derived alert for case ${selectedAlert.case_id}`
                : ""}
            </DialogDescription>
          </DialogHeader>

          {selectedAlert && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-xs text-muted-foreground">ATM</span>
                <strong className="mt-1 block text-sm text-foreground">
                  {selectedAlert.atm_id}
                </strong>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">
                  Risk Score
                </span>
                <strong className="mt-1 block text-sm text-foreground">
                  {riskPercent(selectedAlert.risk_score)}
                </strong>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Severity</span>
                <div className="mt-1">
                  <SeverityBadge level={selectedAlert.severity} />
                </div>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Status</span>
                <div className="mt-1">
                  <StatusBadge status={selectedAlert.status} />
                </div>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Created</span>
                <strong className="mt-1 block text-sm text-foreground">
                  {formatDateTime(selectedAlert.created_at)}
                </strong>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">
                  Acknowledged
                </span>
                <strong className="mt-1 block text-sm text-foreground">
                  {selectedAlert.acknowledged_at
                    ? formatDateTime(selectedAlert.acknowledged_at)
                    : "—"}
                </strong>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Case</span>
                <Link
                  href={`/cases/${selectedAlert.case_id}`}
                  className="mt-1 block text-sm font-semibold text-primary"
                >
                  {selectedAlert.case_id}
                </Link>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">
                  Prediction
                </span>
                <strong className="mt-1 block text-sm text-foreground">
                  {selectedAlert.prediction_id ?? "—"}
                </strong>
              </div>
            </div>
          )}

          <div className="mt-5 rounded-md border border-border bg-muted/50 p-4">
            <strong className="mb-1.5 block text-sm text-foreground">
              Alert Message
            </strong>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {selectedAlert?.message}
            </p>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedAlert(null)}>
              Close
            </Button>
            {selectedAlert && isOpen(selectedAlert.status) && (
              <Button
                onClick={() => void handleAcknowledge(selectedAlert.alert_id)}
              >
                Acknowledge Alert
              </Button>
            )}
            {selectedAlert && isAcknowledged(selectedAlert.status) && (
              <Button
                className="bg-green-700 hover:bg-green-800"
                onClick={() => void handleResolve(selectedAlert.alert_id)}
              >
                Resolve Alert
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}