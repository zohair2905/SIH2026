export interface AuthSession {
  name: string;
  badge: string;
  email: string;
  org: string;
  loginAt: string;
}

const SESSION_KEY = "pcip.session";

export function getSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.sessionStorage.getItem(SESSION_KEY);

    if (!raw) {
      return null;
    }

    return JSON.parse(raw) as AuthSession;
  } catch {
    return null;
  }
}

export function setSession(session: AuthSession) {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSession() {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(SESSION_KEY);
}