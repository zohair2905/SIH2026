import type { AuthSession } from "@/lib/auth";
import { setSession } from "@/lib/auth";

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResult {
  ok: boolean;
  mocked: boolean;
  session?: AuthSession;
  error?: string;
}

const mockSession: AuthSession = {
  name: "Insp. A. Patil",
  badge: "AP",
  email: "a.patil@cic.gov.in",
  org: "Maharashtra Police",
  loginAt: new Date().toLocaleString("en-IN"),
};

export async function login(
  credentials: LoginCredentials
): Promise<LoginResult> {
  try {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
      credentials: "include",
    });

    if (response.ok) {
      const data = await response.json();

      const session: AuthSession = {
        name: data.user?.name ?? mockSession.name,
        badge: data.user?.badge ?? mockSession.badge,
        email: data.user?.email ?? credentials.email,
        org: data.user?.org ?? mockSession.org,
        loginAt: new Date().toLocaleString("en-IN"),
      };

      setSession(session);
      return { ok: true, mocked: false, session };
    }

    return {
      ok: false,
      mocked: false,
      error: (await response.json().catch(() => null))?.detail ??
        "Invalid credentials.",
    };
  } catch {
    // Backend unavailable: accept the demo login and record a stub session.
    setSession(mockSession);
    return { ok: true, mocked: true, session: mockSession };
  }
}

export async function getMe(): Promise<AuthSession | null> {
  try {
    const response = await fetch("/api/auth/me", { credentials: "include" });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();

    return {
      name: data.user?.name ?? "Unknown User",
      badge: data.user?.badge ?? "U",
      email: data.user?.email ?? "",
      org: data.user?.org ?? "Law Enforcement",
      loginAt: new Date().toLocaleString("en-IN"),
    };
  } catch {
    return null;
  }
}