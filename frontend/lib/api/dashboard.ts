import { apiGet, type ApiResult } from "@/lib/api/common";
import type { DashboardOverview } from "@/types";

export async function getDashboard(): Promise<ApiResult<DashboardOverview | null>> {
  const data = await apiGet<DashboardOverview>("/api/dashboard");
  return { data, mocked: data === null };
}