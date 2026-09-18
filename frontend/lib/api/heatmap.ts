import { apiGet, withMock, type ApiResult } from "@/lib/api/common";
import { gisLocations } from "@/mocks/gis";
import type { HeatmapResponse } from "@/types";

const mockHeatmapResponse: HeatmapResponse = {
  case_id: null,
  points: gisLocations.map((location) => ({
    atm_id: location.name,
    latitude: location.position[0],
    longitude: location.position[1],
    risk_score: location.score / 100,
    best_rank: 1,
    observation_count: location.cases,
    severity: location.risk,
    confidence: 0.7,
    top_factors: [],
    area_type: location.area,
    window_start: null,
    window_end: null,
    synthetic_location_data: true,
  })),
};

export async function getHeatmap(): Promise<ApiResult<HeatmapResponse>> {
  return withMock(apiGet<HeatmapResponse>("/api/heatmap"), mockHeatmapResponse);
}