import { NextResponse } from "next/server";

import type { AuthSession } from "@/lib/auth";

const demoUsers: Record<string, AuthSession> = {
  "a.patil@cic.gov.in": {
    name: "Insp. A. Patil",
    badge: "AP",
    email: "a.patil@cic.gov.in",
    org: "Maharashtra Police",
    loginAt: new Date().toLocaleString("en-IN"),
  },
};

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const email = (body?.email ?? "").toString().toLowerCase();
  const password = (body?.password ?? "").toString();

  const user = demoUsers[email];

  if (!user || password.length < 4) {
    return NextResponse.json(
      { detail: "Invalid user ID or password." },
      { status: 401 }
    );
  }

  return NextResponse.json({ user });
}