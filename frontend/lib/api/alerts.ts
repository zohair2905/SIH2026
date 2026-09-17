import { apiGet, apiPost, withMock, type ApiResult } from "@/lib/api/common";
import type { AlertSummary } from "@/types";
import { initialAlerts } from "@/mocks/alerts";

export async function getAlerts(): Promise<ApiResult<AlertSummary[]>> {
  return withMock(apiGet<AlertSummary[]>("/api/alerts"), initialAlerts);
}

export async function acknowledgeAlert(
  id: string
): Promise<ApiResult<AlertSummary>> {
  const fallback =
    initialAlerts.find((a) => a.id === id) ?? initialAlerts[0];

  return withMock(
    apiPost<AlertSummary>(`/api/alerts/${id}/acknowledge`, { status: "acknowledged" }),
    { ...fallback, status: "acknowledged" }
  );
}

export async function resolveAlert(id: string): Promise<ApiResult<AlertSummary>> {
  const fallback =
    initialAlerts.find((a) => a.id === id) ?? initialAlerts[0];

  return withMock(
    apiPost<AlertSummary>(`/api/alerts/${id}/acknowledge`, { status: "resolved" }),
    { ...fallback, status: "resolved" }
  );
}