import { NextResponse } from "next/server";

import type { AuthSession } from "@/lib/auth";

const stubUser: AuthSession = {
  name: "Insp. A. Patil",
  badge: "AP",
  email: "a.patil@cic.gov.in",
  org: "Maharashtra Police",
  loginAt: new Date().toLocaleString("en-IN"),
};

export async function GET() {
  return NextResponse.json({ user: stubUser });
}