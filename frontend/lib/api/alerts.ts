import { apiGet, apiPatch, apiPost, withMock, type ApiResult } from "@/lib/api/common";
import type { AlertRecord } from "@/types";

export async function getAlerts(): Promise<ApiResult<AlertRecord[]>> {
  return withMock(apiGet<AlertRecord[]>("/api/alerts"), []);
}

export async function acknowledgeAlert(id: number): Promise<AlertRecord | null> {
  return apiPost<AlertRecord>(`/api/alerts/${id}/acknowledge`);
}

export async function resolveAlert(id: number): Promise<AlertRecord | null> {
  return apiPatch<AlertRecord>(`/api/alerts/${id}`, { status: "resolved" });
}