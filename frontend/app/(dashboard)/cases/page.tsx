"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Bell,
  ChevronLeft,
  ChevronRight,
  Eye,
  FileText,
  Filter,
  Plus,
  RefreshCw,
  Search,
  TrendingUp,
  Users,
} from "lucide-react";
import { toast } from "sonner";

import { PageHeading } from "@/components/layout/page-heading";
import { SeverityBadge, StatusBadge } from "@/components/badges";
import { Panel } from "@/components/ui/panel";
import { ScoreChip } from "@/components/ui/score-chip";
import { StatCard } from "@/components/ui/stat-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { getCases, registerCase } from "@/lib/api/cases";
import type { CaseRecord, CaseStatus, SeverityLevel } from "@/types";

const crimeTypes = [
  "UPI Fraud",
  "Banking Fraud",
  "Investment Fraud",
  "Phishing",
  "Card Fraud",
  "OTP Fraud",
  "Online Shopping Fraud",
];

interface CaseRow {
  id: string;
  date: string;
  title: string;
  location: string;
  amount: string;
  risk: SeverityLevel | null;
  score: string;
  status: CaseStatus;
  officer: string;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function toRow(record: CaseRecord): CaseRow {
  const prediction = record.prediction;
  return {
    id: record.case_id,
    date: formatDate(record.created_at),
    title: record.title,
    location: prediction?.city ?? "—",
    amount:
      record.amount !== null
        ? `₹${record.amount.toLocaleString("en-IN")}`
        : "—",
    risk: prediction?.severity ?? null,
    score: prediction ? `${Math.round(prediction.risk_score * 100)}%` : "—",
    status: record.status,
    officer: "—",
  };
}

export default function CasesPage() {
  const [cases, setCases] = useState<CaseRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [showForm, setShowForm] = useState(false);

  const [formData, setFormData] = useState({
    transactionId: "",
    type: "UPI Fraud",
    amount: "",
    description: "",
  });

  const load = useCallback(() => {
    getCases().then((result) => {
      setCases(result.data.map(toRow));
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

  const filteredCases = cases.filter((item) => {
    const matchesSearch =
      item.id.toLowerCase().includes(search.toLowerCase()) ||
      item.title.toLowerCase().includes(search.toLowerCase()) ||
      item.location.toLowerCase().includes(search.toLowerCase());

    const matchesRisk =
      riskFilter === "All" || item.risk === riskFilter.toLowerCase();

    const matchesStatus =
      statusFilter === "All" || item.status === statusFilter.toLowerCase();

    return matchesSearch && matchesRisk && matchesStatus;
  });

  const highRiskCount = cases.filter(
    (c) => c.risk === "high" || c.risk === "critical"
  ).length;
  const investigatingCount = cases.filter(
    (c) => c.status === "investigating"
  ).length;
  const resolvedCount = cases.filter(
    (c) => c.status === "resolved" || c.status === "closed"
  ).length;

  const handleRegisterCase = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const result = await registerCase({
      transaction_id: formData.transactionId.trim(),
      title: formData.type,
      description: formData.description || undefined,
      case_type: "complaint",
      priority: "medium",
      amount: formData.amount ? Number(formData.amount) : undefined,
    });

    if (result.data === null) {
      toast.error(
        "Could not register the case. Check the transaction ID and that the backend is running."
      );
      return;
    }

    setFormData({ transactionId: "", type: "UPI Fraud", amount: "", description: "" });
    setShowForm(false);
    toast.success(`${result.data.case_id} registered successfully.`);
    await load();
  };

  return (
    <div className="space-y-6">
      <PageHeading
        title="Case Management"
        description="Monitor, investigate and manage cybercrime complaints"
      >
        <span>
          {loading ? "Loading…" : `${cases.length} cases loaded`}
        </span>
        <button
          type="button"
          onClick={refresh}
          className="flex size-8 items-center justify-center rounded-md border border-border bg-card text-muted-foreground"
          aria-label="Refresh cases"
        >
          <RefreshCw className="size-4" />
        </button>
      </PageHeading>

      {offline && (
        <p className="rounded-md border border-border bg-muted/40 px-4 py-2 text-xs text-muted-foreground">
          Backend unreachable — no case data to display.
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={FileText}
          tone="blue"
          value={String(cases.length)}
          label="Total Cases"
          note="All registered complaints"
        />
        <StatCard
          icon={Bell}
          tone="red"
          value={String(highRiskCount)}
          label="High Risk"
          note="Latest prediction severity"
        />
        <StatCard
          icon={TrendingUp}
          tone="orange"
          value={String(investigatingCount)}
          label="Under Investigation"
          note="Currently active cases"
        />
        <StatCard
          icon={Users}
          tone="green"
          value={String(resolvedCount)}
          label="Resolved"
          note="Successfully closed cases"
        />
      </div>

      <Panel
        icon={FileText}
        title="Cybercrime Cases"
        actions={
          <Button size="sm" onClick={() => setShowForm(true)}>
            <Plus className="size-4" /> Register New Case
          </Button>
        }
      >
        <div className="flex flex-wrap items-center gap-3 border-b border-border px-5 py-4">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="w-64 pl-9"
              placeholder="Search Case ID, title or city..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="relative">
            <Filter className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <select
              className="h-9 rounded-md border border-input bg-background pl-9 pr-3 text-sm"
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
            >
              <option value="All">All Risk Levels</option>
              <option value="High">High Risk</option>
              <option value="Medium">Medium Risk</option>
              <option value="Low">Low Risk</option>
            </select>
          </div>

          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="All">All Status</option>
            <option value="open">Open</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                <th className="px-5 py-3">Case ID</th>
                <th className="px-5 py-3">Date</th>
                <th className="px-5 py-3">Title</th>
                <th className="px-5 py-3">Predicted City</th>
                <th className="px-5 py-3">Amount</th>
                <th className="px-5 py-3">Risk</th>
                <th className="px-5 py-3">Risk Score</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Assigned To</th>
                <th className="px-5 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td
                    colSpan={10}
                    className="px-5 py-10 text-center text-sm text-muted-foreground"
                  >
                    Loading cases…
                  </td>
                </tr>
              )}

              {!loading &&
                filteredCases.map((item) => (
                  <tr
                    key={item.id}
                    className="border-b border-border last:border-0 hover:bg-muted/50"
                  >
                    <td className="px-5 py-3">
                      <Link
                        href={`/cases/${item.id}`}
                        className="font-semibold text-primary"
                      >
                        {item.id}
                      </Link>
                    </td>
                    <td className="px-5 py-3">{item.date}</td>
                    <td className="px-5 py-3">{item.title}</td>
                    <td className="px-5 py-3">{item.location}</td>
                    <td className="px-5 py-3 font-medium">{item.amount}</td>
                    <td className="px-5 py-3">
                      {item.risk ? (
                        <SeverityBadge level={item.risk} />
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      {item.risk ? (
                        <ScoreChip score={item.score} level={item.risk} />
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="px-5 py-3">{item.officer}</td>
                    <td className="px-5 py-3">
                      <Button asChild size="sm" variant="outline">
                        <Link href={`/cases/${item.id}`}>
                          <Eye className="size-3.5" /> View
                        </Link>
                      </Button>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>

          {!loading && filteredCases.length === 0 && (
            <div className="py-10 text-center text-sm text-muted-foreground">
              No cases found matching your filters.
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-5 py-3 text-xs text-muted-foreground">
          <span>
            Showing {filteredCases.length} of {cases.length} cases
          </span>
          <div className="flex items-center gap-1">
            <button
              type="button"
              className="flex size-8 items-center justify-center rounded-md border border-border"
            >
              <ChevronLeft className="size-4" />
            </button>
            <button
              type="button"
              className="flex size-8 items-center justify-center rounded-md bg-primary text-white"
            >
              1
            </button>
            <button
              type="button"
              className="flex size-8 items-center justify-center rounded-md border border-border"
            >
              <ChevronRight className="size-4" />
            </button>
          </div>
        </div>
      </Panel>

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Register New Case</DialogTitle>
            <DialogDescription>
              Enter the complaint details below
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleRegisterCase} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="transactionId">Transaction ID</Label>
              <Input
                id="transactionId"
                placeholder="Example: TXN000000294"
                value={formData.transactionId}
                onChange={(e) =>
                  setFormData((previous) => ({
                    ...previous,
                    transactionId: e.target.value,
                  }))
                }
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="crimeType">Complaint Type</Label>
              <select
                id="crimeType"
                className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={formData.type}
                onChange={(e) =>
                  setFormData((previous) => ({
                    ...previous,
                    type: e.target.value,
                  }))
                }
                required
              >
                {crimeTypes.map((type) => (
                  <option key={type}>{type}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="amount">Amount Involved</Label>
              <Input
                id="amount"
                type="number"
                placeholder="Example: 85000"
                min="0"
                value={formData.amount}
                onChange={(e) =>
                  setFormData((previous) => ({
                    ...previous,
                    amount: e.target.value,
                  }))
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Complaint Description</Label>
              <textarea
                id="description"
                className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Enter a brief description of the complaint..."
                value={formData.description}
                onChange={(e) =>
                  setFormData((previous) => ({
                    ...previous,
                    description: e.target.value,
                  }))
                }
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </Button>
              <Button type="submit">
                <Plus className="size-4" /> Register Case
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}