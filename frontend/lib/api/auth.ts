import type { AuthSession, UserRole } from "@/lib/auth";
import { setSession, clearSession } from "@/lib/auth";

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResult {
  ok: boolean;
  session?: AuthSession;
  error?: string;
}

export interface MeResult {
  ok: boolean;
  session?: AuthSession;
  error?: string;
}

const ORG_LABEL: Record<UserRole, string> = {
  admin: "Administrator",
  investigator: "Investigator",
  analyst: "Intelligence Analyst",
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

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      return {
        ok: false,
        error: data?.detail ?? "Invalid user ID or password.",
      };
    }

    const user = data?.user;
    if (!user) {
      return { ok: false, error: "The authentication service returned no user." };
    }

    const session: AuthSession = {
      id: user.id,
      badge: user.badge ?? "",
      name: user.name ?? "Officer",
      email: user.email ?? credentials.email,
      role: user.role ?? "investigator",
      org: ORG_LABEL[user.role as UserRole] ?? "Law Enforcement",
      loginAt: new Date().toLocaleString("en-IN"),
    };

    setSession(session);
    return { ok: true, session };
  } catch {
    return { ok: false, error: "Backend unreachable. Please try again." };
  }
}

export async function getMe(): Promise<MeResult> {
  try {
    const response = await fetch("/api/auth/me", { credentials: "include" });

    if (!response.ok) {
      return { ok: false };
    }

    const user = (await response.json())?.user;
    if (!user) {
      return { ok: false };
    }

    const session: AuthSession = {
      id: user.id,
      badge: user.badge ?? "",
      name: user.name ?? "Officer",
      email: user.email ?? "",
      role: user.role ?? "investigator",
      org: ORG_LABEL[user.role as UserRole] ?? "Law Enforcement",
      loginAt: new Date().toLocaleString("en-IN"),
    };

    setSession(session);
    return { ok: true, session };
  } catch {
    return { ok: false };
  }
}

export async function logout(): Promise<void> {
  try {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
  } catch {
    // Local logout remains valid even if the backend is unreachable.
  }
  clearSession();
}