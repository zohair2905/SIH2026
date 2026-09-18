import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { backendUrl, sessionCookieName, tokenTtlSeconds } from "@/lib/env";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));

  const upstream = await fetch(`${backendUrl()}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const data = await upstream.json().catch(() => ({}));

  if (!upstream.ok) {
    return NextResponse.json(
      { detail: data?.detail ?? "Invalid user ID or password." },
      { status: upstream.status }
    );
  }

  const token = data?.access_token;
  if (!token) {
    return NextResponse.json(
      { detail: "The authentication service returned no session." },
      { status: 502 }
    );
  }

  (await cookies()).set(sessionCookieName(), token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: tokenTtlSeconds(),
  });

  return NextResponse.json({ user: data.user });
}