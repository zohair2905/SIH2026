import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { backendUrl, sessionCookieName } from "@/lib/env";

export async function POST() {
  const cookieStore = await cookies();
  const token = cookieStore.get(sessionCookieName())?.value;

  if (token) {
    await fetch(`${backendUrl()}/api/auth/logout`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
  }

  cookieStore.delete(sessionCookieName());
  return NextResponse.json({ ok: true });
}