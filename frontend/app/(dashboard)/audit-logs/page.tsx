"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  CheckCircle,
  Eye,
  RefreshCw,
  Search,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";

import { PageHeading } from "@/components/layout/page-heading";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { getAuditLogs, type AuditLogEntry } from "@/lib/api/audit-logs";

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString("en-IN");
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);

  const load = useCallback(() => {
    getAuditLogs().then((entries) => {
      setLogs(entries);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filteredLogs = logs.filter((log) => {
    const text =
      `${log.id} ${log.actor ?? ""} ${log.action} ${log.resource_type} ${log.resource_id ?? ""}`.toLowerCase();

    return text.includes(search.toLowerCase());
  });

  const refresh = () => {
    setLoading(true);
    load();
    toast.success("Audit logs refreshed");
  };

  const serverTimestamps = logs.length;
  const uniqueUsers = new Set(logs.map((l) => l.actor)).size;

  return (
    <div className="space-y-6">
      <PageHeading
        title="Audit Logs"
        description="Monitor user activity and security events across the platform"
      >
        <Button size="sm" variant="outline" onClick={refresh}>
          <RefreshCw className="size-3.5" /> Refresh
        </Button>
      </PageHeading>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex size-10 items-center justify-center rounded-md bg-accent text-primary">
            <Activity className="size-5" />
          </div>
          <div>
            <span className="block text-xs text-muted-foreground">
              Total Events
            </span>
            <strong className="block text-xl text-foreground">
              {serverTimestamps}
            </strong>
            <small className="block text-xs text-muted-foreground">
              Recorded
            </small>
          </div>
        </div>

        <div className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex size-10 items-center justify-center rounded-md bg-green-100 text-green-700">
            <CheckCircle className="size-5" />
          </div>
          <div>
            <span className="block text-xs text-muted-foreground">
              Successful
            </span>
            <strong className="block text-xl text-foreground">
              {serverTimestamps}
            </strong>
            <small className="block text-xs text-muted-foreground">
              Events
            </small>
          </div>
        </div>

        <div className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex size-10 items-center justify-center rounded-md bg-red-100 text-red-600">
            <XCircle className="size-5" />
          </div>
          <div>
            <span className="block text-xs text-muted-foreground">Failed</span>
            <strong className="block text-xl text-foreground">
              {logs.filter((l) => l.action === "auth.login_failed").length}
            </strong>
            <small className="block text-xs text-muted-foreground">
              Login attempts
            </small>
          </div>
        </div>

        <div className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex size-10 items-center justify-center rounded-md bg-purple-100 text-purple-700">
            <Activity className="size-5" />
          </div>
          <div>
            <span className="block text-xs text-muted-foreground">
              Unique Users
            </span>
            <strong className="block text-xl text-foreground">
              {uniqueUsers}
            </strong>
            <small className="block text-xs text-muted-foreground">
              Active
            </small>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="w-64 pl-9"
            placeholder="Search audit logs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <Panel icon={Activity} title="Security Audit Events">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                <th className="px-5 py-3">Event</th>
                <th className="px-5 py-3">Date & Time</th>
                <th className="px-5 py-3">User</th>
                <th className="px-5 py-3">Action</th>
                <th className="px-5 py-3">Target</th>
                <th className="px-5 py-3">IP Address</th>
                <th className="px-5 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-5 py-10 text-center text-sm text-muted-foreground"
                  >
                    Loading audit events…
                  </td>
                </tr>
              )}

              {!loading &&
                filteredLogs.map((log) => (
                  <tr
                    key={log.id}
                    className="border-b border-border last:border-0 hover:bg-muted/50"
                  >
                    <td className="px-5 py-3 font-medium text-muted-foreground">
                      {log.id}
                    </td>
                    <td className="px-5 py-3 whitespace-nowrap">
                      {formatDateTime(log.created_at)}
                    </td>
                    <td className="px-5 py-3">{log.actor ?? "—"}</td>
                    <td className="px-5 py-3 font-medium text-foreground">
                      {log.action}
                    </td>
                    <td className="px-5 py-3">
                      {log.resource_id ?? log.resource_type}
                    </td>
                    <td className="px-5 py-3">{log.ip_address ?? "—"}</td>
                    <td className="px-5 py-3">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedLog(log)}
                      >
                        <Eye className="size-3.5" /> View
                      </Button>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>

          {!loading && filteredLogs.length === 0 && (
            <div className="py-10 text-center text-sm text-muted-foreground">
              No audit events found matching your filters.
            </div>
          )}
        </div>
      </Panel>

      <Dialog
        open={selectedLog !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedLog(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Audit Event Details</DialogTitle>
          </DialogHeader>
          {selectedLog &&
            (
              [
                ["Event", String(selectedLog.id)],
                ["Date & Time", formatDateTime(selectedLog.created_at)],
                ["User", selectedLog.actor ?? "—"],
                ["Action", selectedLog.action],
                ["Resource", selectedLog.resource_type],
                ["Target", selectedLog.resource_id ?? "—"],
                ["IP Address", selectedLog.ip_address ?? "—"],
                [
                  "Details",
                  JSON.stringify(selectedLog.details ?? {}, null, 2),
                ],
              ] as const
            ).map(([label, value]) => (
              <div
                key={label}
                className="flex items-center justify-between border-b border-border py-2.5 last:border-0"
              >
                <span className="text-sm text-muted-foreground">{label}</span>
                <strong className="text-sm text-foreground">{value}</strong>
              </div>
            ))}
        </DialogContent>
      </Dialog>
    </div>
  );
}