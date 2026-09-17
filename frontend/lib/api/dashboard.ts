import { apiGet, withMock, type ApiResult } from "@/lib/api/common";
import type { DashboardOverview } from "@/types";
import {
  dashboardKPIs,
  predictedLocations,
  recentAlerts,
} from "@/mocks/dashboard";

const mockOverview: DashboardOverview = {
  kpis: dashboardKPIs,
  predictedLocations,
  recentAlerts,
};

export interface DashboardQuery {
  days?: number;
  district?: string;
}

export async function getDashboard(
  query: DashboardQuery = {}
): Promise<ApiResult<DashboardOverview>> {
  const params = new URLSearchParams();

  if (query.days) params.set("days", String(query.days));
  if (query.district) params.set("district", query.district);

  const qs = params.toString();

  return withMock(
    apiGet<DashboardOverview>(`/api/dashboard${qs ? `?${qs}` : ""}`),
    mockOverview
  );
}