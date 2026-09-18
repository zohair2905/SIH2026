import { apiGet, apiPost, withMock, type ApiResult } from "@/lib/api/common";
import type { PredictionResult, PredictionRun, PredictionRunInput } from "@/types";
import { latestPredictions as predictedLocations } from "@/mocks/predictions";

const mockResult: PredictionResult = {
  id: "PRED-2026-0917",
  status: "completed",
  generatedAt: new Date().toLocaleString("en-IN"),
  locations: predictedLocations,
};

export async function runPrediction(
  input: PredictionRunInput
): Promise<ApiResult<PredictionResult>> {
  return withMock(apiPost<PredictionResult>("/api/predictions", input), mockResult);
}

export async function getPrediction(
  id: string
): Promise<ApiResult<PredictionResult>> {
  return withMock(apiGet<PredictionResult>(`/api/predictions/${id}`), mockResult);
}

export async function getPredictionRun(
  id: string
): Promise<ApiResult<PredictionRun | null>> {
  const result = await apiGet<PredictionRun>(`/api/predictions/${id}`);
  return { data: result, mocked: result === null };
}