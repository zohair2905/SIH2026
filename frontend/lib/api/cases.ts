import { apiGet, apiPost, withMock, type ApiResult } from "@/lib/api/common";
import type {
  CaseNetwork,
  CaseSummary,
  CaseTransaction,
} from "@/types";
import { initialCases } from "@/mocks/cases";

export interface RegisterCaseInput {
  date: string;
  type: string;
  location: string;
  amount: string;
  officer?: string;
  description?: string;
}

function nextCaseNumber(base: number): string {
  return `CC-2026-${base + 1}`;
}

export async function getCases(): Promise<ApiResult<CaseSummary[]>> {
  return withMock(apiGet<CaseSummary[]>("/api/cases"), initialCases);
}

export async function registerCase(
  input: RegisterCaseInput
): Promise<ApiResult<CaseSummary>> {
  const mockCase: CaseSummary = {
    id: nextCaseNumber(+initialCases[0].id.split("-")[2]),
    date: input.date || new Date().toLocaleDateString("en-IN"),
    type: input.type,
    location: input.location,
    amount: input.amount,
    risk: "medium",
    score: "—",
    status: "new",
    officer: input.officer ?? "Unassigned",
  };

  return withMock(
    apiPost<CaseSummary>("/api/cases", input),
    mockCase
  );
}

export async function getCaseDetail(
  id: string
): Promise<ApiResult<CaseSummary | null>> {
  const fallback = initialCases.find((c) => c.id === id) ?? null;

  return withMock(
    apiGet<CaseSummary>(`/api/cases/${id}`),
    fallback
  );
}

const mockTransactions: Record<string, CaseTransaction[]> = {
  "CC-2026-4381": [
    {
      id: "TXN-98421",
      date: "14 Sep 2026, 16:42",
      bank: "HDFC Bank",
      channel: "ATM",
      amount: "₹20,000",
      status: "Frozen",
    },
    {
      id: "TXN-98397",
      date: "14 Sep 2026, 16:05",
      bank: "HDFC Bank",
      channel: "UPI",
      amount: "₹45,000",
      status: "Frozen",
    },
    {
      id: "TXN-98310",
      date: "14 Sep 2026, 15:38",
      bank: "ICICI Bank",
      channel: "UPI",
      amount: "₹20,000",
      status: "Frozen",
    },
  ],
};

const mockNetworks: Record<string, CaseNetwork> = {
  "CC-2026-4381": {
    nodes: [
      { id: "AC-778492", role: "Originating", risk: "high" },
      { id: "AC-903114", role: "Skimmer", risk: "high" },
      { id: "AC-661208", role: "Mule", risk: "medium" },
      { id: "AC-172930", role: "Beneficiary", risk: "low" },
    ],
    links: [
      { source: "AC-778492", target: "AC-903114" },
      { source: "AC-903114", target: "AC-661208" },
      { source: "AC-661208", target: "AC-172930" },
    ],
  },
};

export async function getTransactions(
  id: string
): Promise<ApiResult<CaseTransaction[]>> {
  return withMock(
    apiGet<CaseTransaction[]>(`/api/cases/${id}/transactions`),
    mockTransactions[id] ?? []
  );
}

export async function getNetwork(
  id: string
): Promise<ApiResult<CaseNetwork>> {
  return withMock(
    apiGet<CaseNetwork>(`/api/cases/${id}/network`),
    mockNetworks[id] ?? { nodes: [], links: [] }
  );
}