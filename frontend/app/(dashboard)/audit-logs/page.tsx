"use client";

import { useState } from "react";
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
import { initialLogs } from "@/mocks/audit-logs";
import type { AuditLog } from "@/types";

export default function AuditLogsPage() {
  const [logs, setLogs] = useState(initialLogs);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("All");
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const filteredLogs = logs.filter((log) => {
    const text = `${log.id} ${log.user} ${log.action} ${log.target}`.toLowerCase();

    return (
      text.includes(search.toLowerCase()) &&
      (status === "All" || log.status === status)
    );
  });

  const refreshLogs = () => {
    setLogs([...initialLogs]);
    toast.success("Audit logs refreshed");
  };

  return (
    <div className="space-y-6">
      <PageHeading
        title="Audit Logs"
        description="Monitor user activity and security events across the platform"
      >
        <Button size="sm" variant="outline" onClick={refreshLogs}>
          <RefreshCw className="size-3.5" /> Refresh
        </Button>
      </PageHeading>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            icon: Activity,
            iconBg: "bg-accent text-primary",
            label: "Total Events",
            value: logs.length,
            note: "Recorded",
          },
          {
            icon: CheckCircle,
            iconBg: "bg-green-100 text-green-700",
            label: "Successful",
            value: logs.filter((l) => l.status === "Success").length,
            note: "Events",
          },
          {
            icon: XCircle,
            iconBg: "bg-red-100 text-red-600",
            label: "Failed",
            value: logs.filter((l) => l.status === "Failed").length,
            note: "Events",
          },
          {
            icon: Activity,
            iconBg: "bg-purple-100 text-purple-700",
            label: "Active Users",
            value: "5",
            note: "Today",
          },
        ].map(({ icon: Icon, iconBg, label, value, note }) => (
          <div
            key={label}
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm"
          >
            <div
              className={`flex size-10 items-center justify-center rounded-md ${iconBg}`}
            >
              <Icon className="size-5" />
            </div>
            <div>
              <span className="block text-xs text-muted-foreground">
                {label}
              </span>
              <strong className="block text-xl text-foreground">{value}</strong>
              <small className="block text-xs text-muted-foreground">
                {note}
              </small>
            </div>
          </div>
        ))}
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

        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="All">All Status</option>
          <option value="Success">Success</option>
          <option value="Failed">Failed</option>
        </select>
      </div>

      <Panel icon={Activity} title="Security Audit Events">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                <th className="px-5 py-3">Log ID</th>
                <th className="px-5 py-3">Date & Time</th>
                <th className="px-5 py-3">User</th>
                <th className="px-5 py-3">Action</th>
                <th className="px-5 py-3">Target</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">IP Address</th>
                <th className="px-5 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log) => (
                <tr
                  key={log.id}
                  className="border-b border-border last:border-0 hover:bg-muted/50"
                >
                  <td className="px-5 py-3 font-medium text-muted-foreground">
                    {log.id}
                  </td>
                  <td className="px-5 py-3">{log.date}</td>
                  <td className="px-5 py-3">{log.user}</td>
                  <td className="px-5 py-3 font-medium text-foreground">
                    {log.action}
                  </td>
                  <td className="px-5 py-3">{log.target}</td>
                  <td className="px-5 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                        log.status === "Success"
                          ? "bg-green-100 text-green-700"
                          : "bg-red-100 text-red-600"
                      }`}
                    >
                      {log.status}
                    </span>
                  </td>
                  <td className="px-5 py-3">{log.ip}</td>
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

          {filteredLogs.length === 0 && (
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
                ["Log ID", selectedLog.id],
                ["Date & Time", selectedLog.date],
                ["User", selectedLog.user],
                ["Action", selectedLog.action],
                ["Target", selectedLog.target],
                ["Status", selectedLog.status],
                ["IP Address", selectedLog.ip],
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