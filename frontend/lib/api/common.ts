export async function apiGet<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(path, { credentials: "include" });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function apiPost<T>(
  path: string,
  body?: unknown
): Promise<T | null> {
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      credentials: "include",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function apiPatch<T>(
  path: string,
  body?: unknown
): Promise<T | null> {
  try {
    const response = await fetch(path, {
      method: "PATCH",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      credentials: "include",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export interface ApiResult<T> {
  data: T;
  mocked: boolean;
}

export async function withMock<T>(
  request: Promise<T | null>,
  mock: T
): Promise<ApiResult<T>> {
  const data = await request;
  return data === null ? { data: mock, mocked: true } : { data, mocked: false };
}