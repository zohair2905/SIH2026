import { apiGet, apiPost, withMock, type ApiResult } from "@/lib/api/common";
import type { PredictionResult, PredictionRunInput } from "@/types";
import { predictedLocations } from "@/mocks/dashboard";

const mockResult: PredictionResult = {
  id: "PRED-2026-0917",
  status: "completed",
  generatedAt: new Date().toLocaleString("en-IN"),
  locations: predictedLocations,
};

export async function runPrediction(
  input: PredictionRunInput
): Promise<ApiResult<PredictionResult>> {
  return withMock(
    apiPost<PredictionResult>("/api/predictions", input),
    mockResult
  );
}

export async function getPrediction(
  id: string
): Promise<ApiResult<PredictionResult>> {
  return withMock(
    apiGet<PredictionResult>(`/api/predictions/${id}`),
    mockResult
  );
}