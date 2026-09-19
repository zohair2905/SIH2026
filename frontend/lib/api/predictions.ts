import { apiGet, type ApiResult } from "@/lib/api/common";
import type { PredictionRun } from "@/types";

export async function getPredictionRun(
  id: string
): Promise<ApiResult<PredictionRun | null>> {
  const result = await apiGet<PredictionRun>(`/api/predictions/${id}`);
  return { data: result, mocked: result === null };
}