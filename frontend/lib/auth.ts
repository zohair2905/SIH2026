export interface AuthSession {
  id: number;
  badge: string;
  name: string;
  email: string;
  role: "admin" | "investigator" | "analyst";
  org: string;
  loginAt: string;
}

export type UserRole = AuthSession["role"];

const SESSION_KEY = "pcip.session";
export const SESSION_EVENT = "sih:session";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function getSession(): AuthSession | null {
  if (!isBrowser()) {
    return null;
  }

  try {
    const raw = window.sessionStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as AuthSession) : null;
  } catch {
    return null;
  }
}

export function setSession(session: AuthSession) {
  if (!isBrowser()) {
    return;
  }

  window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  window.dispatchEvent(new Event(SESSION_EVENT));
}

export function clearSession() {
  if (!isBrowser()) {
    return;
  }

  window.sessionStorage.removeItem(SESSION_KEY);
  window.dispatchEvent(new Event(SESSION_EVENT));
}

export function isOperator(role: UserRole | undefined): boolean {
  return role === "investigator" || role === "admin";
}

export function isAdmin(role: UserRole | undefined): boolean {
  return role === "admin";
}

import { useEffect, useState } from "react";

export function useSession(): AuthSession | null {
  const [session, setCurrent] = useState<AuthSession | null>(() =>
    getSession()
  );

  useEffect(() => {
    const sync = () => setCurrent(getSession());
    sync();
    window.addEventListener(SESSION_EVENT, sync);
    return () => window.removeEventListener(SESSION_EVENT, sync);
  }, []);

  return session;
}