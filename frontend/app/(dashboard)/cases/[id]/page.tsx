"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Clock,
  FileSearch,
  FileText,
  IndianRupee,
  Map,
  MapPin,
  Plus,
  TrendingUp,
  User,
} from "lucide-react";
import { toast } from "sonner";

import { SeverityBadge, StatusBadge } from "@/components/badges";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Panel } from "@/components/ui/panel";
import {
  addNote,
  getCaseDetail,
  getNetwork,
  getNotes,
  getTransactions,
  runCasePrediction,
  updateCaseStatus,
} from "@/lib/api/cases";
import { getPredictionRun } from "@/lib/api/predictions";
import { isOperator, useSession } from "@/lib/auth";
import type {
  CaseNetwork,
  CaseNote,
  CaseRecord,
  NetworkLink,
  NetworkNode,
  PredictionRun,
  TransactionRecord,
} from "@/types";

type CaseStatusValue = "open" | "investigating" | "resolved" | "closed";

const relationLabel: Record<NetworkLink["relation"], string> = {
  belongs_to: "belongs to (customer account)",
  same_customer: "same customer (other transactions)",
  candidate_withdrawal_point: "candidate withdrawal point (model-derived)",
};

const kindLabel: Record<NetworkNode["kind"], string> = {
  transaction: "Transaction",
  customer: "Account holder",
  atm: "Candidate ATM (model-linked)",
};

function fmtDate(value: string): string {
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

function fmtDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString("en-IN");
}

function fmtAmount(value: number | null): string {
  return value !== null ? `₹${value.toLocaleString("en-IN")}` : "—";
}

function riskPercent(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function NodeItem({ node }: { node: NetworkNode }) {
  return (
    <li className="flex items-start justify-between gap-3 rounded-md border border-border p-3">
      <div className="min-w-0">
        <strong className="block truncate text-sm text-foreground">
          {node.label}
        </strong>
        <span className="text-xs text-muted-foreground">{kindLabel[node.kind]}</span>
      </div>
      {node.kind === "atm" && (
        <span className="shrink-0 text-right text-xs text-muted-foreground">
          rank {String(node.details.candidate_rank ?? "—")}
          <br />
          linked {String(node.details.linked_account_count ?? "—")} · susp.{" "}
          {String(node.details.suspicious_account_count ?? "—")}
        </span>
      )}
      {node.kind === "transaction" && (
        <span className="shrink-0 text-right text-xs text-muted-foreground">
          {fmtAmount(node.details.amount as number | null)}
        </span>
      )}
    </li>
  );
}

export default function CaseDetailsPage() {
  const params = useParams<{ id: string }>();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const session = useSession();
  const canOperate = isOperator(session?.role);

  const [detail, setDetail] = useState<CaseRecord | null>(null);
  const [prediction, setPrediction] = useState<PredictionRun | null>(null);
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [network, setNetwork] = useState<CaseNetwork | null>(null);
  const [notes, setNotes] = useState<CaseNote[]>([]);
  const [noteText, setNoteText] = useState("");
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);
  const [missing, setMissing] = useState(false);
  const [runningPrediction, setRunningPrediction] = useState(false);

  const load = useCallback(() => {
    getCaseDetail(id).then((detailResult) => {
      const current = detailResult.data;

      if (current === null) {
        setDetail(null);
        setMissing(!detailResult.mocked);
        setOffline(detailResult.mocked);
        setLoading(false);
        return;
      }

      setDetail(current);
      setMissing(false);
      setOffline(detailResult.mocked);

      Promise.all([getTransactions(id), getNetwork(id), getNotes(id)]).then(
        ([txResult, networkResult, notesResult]) => {
          setTransactions(txResult.data);
          setNetwork(networkResult.data);
          setNotes(notesResult.data);

          if (current.prediction) {
            getPredictionRun(current.prediction.prediction_id).then((runResult) => {
              setPrediction(runResult.data);
              setLoading(false);
            });
          } else {
            setPrediction(null);
            setLoading(false);
          }
        }
      );
    });
  }, [id]);

  useEffect(() => {
    if (id) {
      void load();
    }
  }, [id, load]);

  const handleStatusChange = async (status: CaseStatusValue) => {
    const updated = await updateCaseStatus(id, status);
    if (updated === null) {
      toast.error("Could not update case status.");
      return;
    }
    setDetail(updated);
    toast.success(`Case status updated to ${status}.`);
  };

  const handleAddNote = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = noteText.trim();
    if (!trimmed) {
      return;
    }
    const actor = session?.name ?? "Investigator";
    const created = await addNote(id, trimmed, actor);
    if (created === null) {
      toast.error("Could not record the note.");
      return;
    }
    setNotes((previous) => [created, ...previous]);
    setNoteText("");
    toast.success("Note recorded.");
  };

  const handleRunPrediction = async () => {
    setRunningPrediction(true);
    const result = await runCasePrediction(id);
    if (result.data === null) {
      toast.error("Prediction could not be run. Is the model available?");
    } else {
      setPrediction(result.data);
      const refreshed = await getCaseDetail(id);
      if (refreshed.data) {
        setDetail(refreshed.data);
      }
      toast.success("Prediction generated.");
    }
    setRunningPrediction(false);
  };

  if (loading) {
    return (
      <div className="py-16 text-center text-sm text-muted-foreground">
        Loading case {id}…
      </div>
    );
  }

  if (missing) {
    return (
      <div className="space-y-6">
        <Link
          href="/cases"
          className="flex w-fit items-center gap-2 text-sm font-medium text-primary"
        >
          <ArrowLeft className="size-4" /> Back to Cases
        </Link>
        <div className="py-16 text-center text-sm text-muted-foreground">
          Case {id} was not found.
        </div>
      </div>
    );
  }

  if (detail === null) {
    return (
      <div className="space-y-6">
        <Link
          href="/cases"
          className="flex w-fit items-center gap-2 text-sm font-medium text-primary"
        >
          <ArrowLeft className="size-4" /> Back to Cases
        </Link>
        {offline && (
          <div className="py-16 text-center text-sm text-muted-foreground">
            Backend unreachable — case data is unavailable.
          </div>
        )}
      </div>
    );
  }

  const top = prediction?.locations[0] ?? null;
  const riskScore = detail.prediction?.risk_score ?? top?.risk_score ?? null;
  const riskSeverity = detail.prediction?.severity ?? top?.severity ?? null;
  const timelineEvents = [
    { title: "Case Registered", time: fmtDateTime(detail.created_at) },
    ...(prediction
      ? [{ title: "Prediction Generated", time: fmtDateTime(prediction.generated_at) }]
      : []),
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
            <h1 className="text-2xl font-semibold text-foreground">Case {detail.case_id}</h1>
            {riskSeverity ? (
              <SeverityBadge level={riskSeverity} />
            ) : (
              <StatusBadge status={detail.status} />
            )}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {detail.title} • Registered on {fmtDate(detail.created_at)}
          </p>
        </div>

        {canOperate && (
          <div className="flex flex-wrap gap-2">
            <select
              className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              value={detail.status}
              onChange={(e) =>
                void handleStatusChange(e.target.value as CaseStatusValue)
              }
              aria-label="Update case status"
            >
              <option value="open">Open</option>
              <option value="investigating">Investigating</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
            <Button
              onClick={() => void handleRunPrediction()}
              disabled={runningPrediction}
            >
              {runningPrediction ? "Running…" : "Run Prediction"}
            </Button>
          </div>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            icon: MapPin,
            label: "Predicted City",
            value: detail.prediction?.city ?? "—",
          },
          {
            icon: IndianRupee,
            label: "Amount Involved",
            value: fmtAmount(detail.amount),
          },
          {
            icon: Activity,
            label: "Risk Score",
            value: riskScore !== null ? riskPercent(riskScore) : "—",
          },
          { icon: User, label: "Assigned Officer", value: "—" },
        ].map(({ icon: Icon, label, value }) => (
          <div
            key={label}
            className="flex items-center gap-4 rounded-lg border border-border bg-card p-5 shadow-sm"
          >
            <div className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-accent text-primary">
              <Icon className="size-5" />
            </div>
            <div className="min-w-0">
              <span className="block text-xs text-muted-foreground">{label}</span>
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
              {[
                ["Case ID", detail.case_id],
                [
                  "Linked Transaction",
                  detail.transaction_id ?? "None",
                ],
                ["Case Type", detail.case_type],
                ["Priority", detail.priority],
              ].map(([label, value]) => (
                <div key={label}>
                  <span className="block text-xs text-muted-foreground">{label}</span>
                  <strong className="mt-1 block text-sm text-foreground">
                    {value}
                  </strong>
                </div>
              ))}
              <div>
                <span className="block text-xs text-muted-foreground">Status</span>
                <StatusBadge status={detail.status} className="mt-1" />
              </div>
              <div>
                <span className="block text-xs text-muted-foreground">Description</span>
                <p className="mt-1 text-sm text-foreground">
                  {detail.description || "—"}
                </p>
              </div>
              <div>
                <span className="block text-xs text-muted-foreground">Created</span>
                <strong className="mt-1 block text-sm text-foreground">
                  {fmtDateTime(detail.created_at)}
                </strong>
              </div>
              <div>
                <span className="block text-xs text-muted-foreground">Last Updated</span>
                <strong className="mt-1 block text-sm text-foreground">
                  {fmtDateTime(detail.updated_at)}
                </strong>
              </div>
            </div>
          </Panel>

          <Panel
            icon={TrendingUp}
            title="Predictive Intelligence"
            actions={
              prediction && (
                <Link
                  href={`/predictions/${prediction.prediction_id}`}
                  className="text-xs font-medium text-primary"
                >
                  View Prediction
                </Link>
              )
            }
          >
            {top ? (
              <div className="space-y-4 p-5">
                <div className="flex items-start gap-5 rounded-lg border border-border bg-muted/40 p-5">
                  <div
                    className="flex size-24 shrink-0 items-center justify-center rounded-full border-8 border-risk text-2xl font-bold text-risk"
                  >
                    {top.risk_score_percent.toFixed(0)}%
                  </div>
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Top predicted withdrawal risk
                    </span>
                    <h3 className="mt-1 text-lg font-semibold text-foreground">
                      {top.atm_id} ({top.city ?? "—"})
                    </h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {prediction?.model_name} {prediction?.model_version}.{" "}
                      {prediction?.note}
                    </p>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  {[
                    {
                      icon: Clock,
                      label: "Predicted Window",
                      value: prediction
                        ? `${fmtDate(prediction.window.start)} – ${fmtDate(prediction.window.end)}`
                        : "—",
                    },
                    {
                      icon: MapPin,
                      label: "Predicted Area",
                      value: top.area_type ?? "—",
                    },
                    {
                      icon: Activity,
                      label: "Confidence",
                      value: `${top.risk_score_percent.toFixed(0)}%`,
                    },
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
            ) : (
              <div className="p-5 text-sm text-muted-foreground">
                No prediction has been run for this case yet. Run one to see ranked
                withdrawal locations and evidence.
              </div>
            )}
          </Panel>

          <Panel icon={IndianRupee} title="Transactions">
            <div className="overflow-x-auto">
              {transactions.length === 0 ? (
                <div className="p-5 text-sm text-muted-foreground">
                  No linked transaction history.
                </div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
                      <th className="px-5 py-3">Transaction</th>
                      <th className="px-5 py-3">Timestamp</th>
                      <th className="px-5 py-3">Channel</th>
                      <th className="px-5 py-3">Type</th>
                      <th className="px-5 py-3">Amount</th>
                      <th className="px-5 py-3">KYC</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx) => (
                      <tr
                        key={tx.transaction_id}
                        className="border-b border-border last:border-0"
                      >
                        <td className="px-5 py-3 font-medium">
                          {tx.transaction_id}
                        </td>
                        <td className="px-5 py-3">
                          {tx.timestamp ? fmtDateTime(tx.timestamp) : "—"}
                        </td>
                        <td className="px-5 py-3">{tx.channel ?? "—"}</td>
                        <td className="px-5 py-3">{tx.transaction_type ?? "—"}</td>
                        <td className="px-5 py-3 font-medium">
                          {fmtAmount(tx.transaction_amount)}
                        </td>
                        <td className="px-5 py-3">{tx.kyc_status ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </Panel>

          <Panel icon={FileSearch} title="Investigator Notes">
            <div className="p-5">
              {notes.length === 0 ? (
                <p className="mb-4 text-sm text-muted-foreground">
                  No notes recorded for this case yet.
                </p>
              ) : (
                <ul className="mb-4 space-y-3">
                  {notes.map((note) => (
                    <li
                      key={note.note_id}
                      className="rounded-lg border border-border p-3"
                    >
                      <p className="text-sm text-foreground">{note.note}</p>
                      <p className="mt-2 text-xs text-muted-foreground">
                        {note.actor ?? "Anonymous"} • {fmtDateTime(note.created_at)}
                      </p>
                    </li>
                  ))}
                </ul>
              )}

              {canOperate && (
                <form onSubmit={handleAddNote} className="space-y-2">
                  <Label htmlFor="newNote">Add a note</Label>
                  <textarea
                    id="newNote"
                    className="min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    placeholder="Record an action, a finding or a follow-up…"
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                  />
                  <Button type="submit" size="sm">
                    <Plus className="size-4" /> Add Note
                  </Button>
                </form>
              )}
            </div>
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel icon={AlertTriangle} title="Risk Assessment">
            {riskScore !== null ? (
              <div className="p-5">
                <div className="flex items-end justify-center py-4">
                  <div className="text-center">
                    <strong className="block text-5xl font-bold text-risk">
                      {riskPercent(riskScore)}
                    </strong>
                    <span className="mt-1 block text-sm text-muted-foreground">
                      Top current-run risk score
                    </span>
                  </div>
                </div>

                <div className="mb-5 h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-risk"
                    style={{ width: riskPercent(riskScore) }}
                  />
                </div>

                <div className="space-y-3">
                  {(top?.evidence.top_factors?.length ? top.evidence.top_factors : []).map(
                    (factor) => (
                      <div key={factor} className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">{factor}</span>
                        <span className="text-xs font-semibold text-risk-high">
                          Contributing
                        </span>
                      </div>
                    )
                  )}
                  {!(top?.evidence.top_factors?.length) && (
                    <p className="text-sm text-muted-foreground">
                      No feature-level evidence recorded by this run.
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-5 text-sm text-muted-foreground">
                No prediction run yet — no risk score to display.
              </div>
            )}
          </Panel>

          <Panel icon={Map} title="Predicted Withdrawal">
            {top ? (
              <div className="p-5">
                <div className="mb-4 flex items-center gap-4 rounded-lg border border-border bg-muted/40 p-4">
                  <MapPin className="size-6 shrink-0 text-primary" />
                  <div>
                    <strong className="block text-sm text-foreground">
                      {top.atm_id}
                    </strong>
                    <span className="text-xs text-muted-foreground">
                      {top.city ?? "—"}
                      {top.area_type ? ` • ${top.area_type}` : ""}
                      {top.synthetic_location_data ? " • synthetic coordinates" : ""}
                    </span>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  {[
                    [
                      "Prediction Window",
                      prediction
                        ? `${fmtDate(prediction.window.start)} – ${fmtDate(prediction.window.end)}`
                        : "—",
                    ],
                    ["Risk Score", riskPercent(top.risk_score)],
                    ["Candidate Rank", String(top.candidate_rank)],
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
            ) : (
              <div className="p-5 text-sm text-muted-foreground">
                No prediction to display yet.
              </div>
            )}
          </Panel>

          <Panel icon={Activity} title="Network Relationships">
            <div className="p-5">
              {network && (
                <p className="mb-4 rounded-md border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
                  {network.semantics}
                </p>
              )}
              {network && network.nodes.length > 0 ? (
                <ul className="space-y-2">
                  {network.nodes.map((node) => (
                    <NodeItem key={node.id} node={node} />
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No relationship data to display.
                </p>
              )}
              {network && network.links.length > 0 && (
                <ul className="mt-4 space-y-1">
                  {network.links.map((link) => (
                    <li
                      key={`${link.source}-${link.target}-${link.relation}`}
                      className="flex items-center gap-2 text-xs text-muted-foreground"
                    >
                      <span className="font-medium text-foreground">
                        {link.source.replace("customer:", "")}
                      </span>
                      <span>→</span>
                      <span className="font-medium text-foreground">
                        {link.target}
                      </span>
                      <span className="ml-auto text-right">
                        {relationLabel[link.relation]}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </Panel>

          <Panel icon={Clock} title="Case Timeline">
            <div className="p-5">
              {timelineEvents.length === 0 ? (
                <p className="text-sm text-muted-foreground">No events recorded.</p>
              ) : (
                timelineEvents.map(({ title, time }, index) => (
                  <div
                    key={title}
                    className="relative flex gap-4 pb-5 last:pb-0"
                  >
                    {index < timelineEvents.length - 1 && (
                      <span className="absolute left-4 top-9 h-full w-px bg-border" />
                    )}
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-accent text-primary">
                      <Clock className="size-4" />
                    </div>
                    <div>
                      <strong className="block text-sm text-foreground">
                        {title}
                      </strong>
                      <span className="text-xs text-muted-foreground">{time}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}