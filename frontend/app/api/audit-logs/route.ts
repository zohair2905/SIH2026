import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { backendUrl, sessionCookieName } from "@/lib/env";

export const dynamic = "force-dynamic";

export async function GET() {
  const token = (await cookies()).get(sessionCookieName())?.value;

  if (!token) {
    return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  }

  const upstream = await fetch(`${backendUrl()}/api/audit-logs`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  const data = await upstream.json().catch(() => ({}));

  // Forward backend status including the 403 admin-only gate.
  return NextResponse.json(data, { status: upstream.status });
}