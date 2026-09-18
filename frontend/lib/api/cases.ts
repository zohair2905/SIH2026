import {
  apiGet,
  apiPatch,
  apiPost,
  withMock,
  type ApiResult,
} from "@/lib/api/common";
import type {
  CaseNetwork,
  CaseNote,
  CaseRecord,
  PredictionRun,
  TransactionRecord,
} from "@/types";

export interface RegisterCaseInput {
  transaction_id: string;
  title: string;
  description?: string;
  priority?: "low" | "medium" | "high" | "critical";
  case_type?: "atm_withdrawal" | "complaint";
  amount?: number;
}

export async function getCases(): Promise<ApiResult<CaseRecord[]>> {
  return withMock(apiGet<CaseRecord[]>("/api/cases"), []);
}

export async function registerCase(
  input: RegisterCaseInput
): Promise<ApiResult<CaseRecord | null>> {
  const result = await apiPost<CaseRecord>("/api/cases", input);
  return { data: result, mocked: result === null };
}

export async function getCaseDetail(
  id: string
): Promise<ApiResult<CaseRecord | null>> {
  const result = await apiGet<CaseRecord>(`/api/cases/${id}`);
  return { data: result, mocked: result === null };
}

export async function getTransactions(
  id: string
): Promise<ApiResult<TransactionRecord[]>> {
  return withMock(apiGet<TransactionRecord[]>(`/api/cases/${id}/transactions`), []);
}

export async function getNetwork(id: string): Promise<ApiResult<CaseNetwork>> {
  return withMock(apiGet<CaseNetwork>(`/api/cases/${id}/network`), {
    case_id: id,
    semantics: "Backend unavailable; no relationship data to show.",
    nodes: [],
    links: [],
  });
}

export async function getNotes(id: string): Promise<ApiResult<CaseNote[]>> {
  return withMock(apiGet<CaseNote[]>(`/api/cases/${id}/notes`), []);
}

export async function addNote(
  id: string,
  note: string,
  actor: string | null
): Promise<CaseNote | null> {
  return apiPost<CaseNote>(`/api/cases/${id}/notes`, {
    note,
    actor: actor ?? undefined,
  });
}

export async function updateCaseStatus(
  id: string,
  status: "open" | "investigating" | "resolved" | "closed"
): Promise<CaseRecord | null> {
  return apiPatch<CaseRecord>(`/api/cases/${id}`, { status });
}

export async function runCasePrediction(
  id: string
): Promise<ApiResult<PredictionRun | null>> {
  const result = await apiPost<PredictionRun>(`/api/cases/${id}/predict`);
  return { data: result, mocked: result === null };
}