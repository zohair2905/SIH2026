export function backendUrl(): string {
  return process.env.BACKEND_URL ?? "http://localhost:8000";
}

export function sessionCookieName(): string {
  return process.env.SESSION_COOKIE_NAME ?? "sih_access_token";
}

export function tokenTtlSeconds(): number {
  const hours = Number(process.env.ACCESS_TOKEN_TTL_HOURS ?? 12);
  return Number.isFinite(hours) && hours > 0 ? hours * 3600 : 12 * 3600;
}