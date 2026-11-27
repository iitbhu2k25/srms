import useSWR, { type SWRConfiguration } from "swr";

// Same-origin: the Next.js server forwards /api/* to the FastAPI backend (src/app/api/[...path]/route.ts).
export const API_BASE = "/api";

export class ApiError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
  }
}

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return typeof body.detail === "string" ? body.detail : `${res.status} ${res.statusText}`;
  } catch {
    return `${res.status} ${res.statusText}`;
  }
}

export async function fetcher<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new ApiError(await errorMessage(res), res.status);
  return res.json();
}

/** Sends JSON; returns the parsed response. */
export async function sendApi<T = unknown>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new ApiError(await errorMessage(res), res.status);
  return res.status === 204 ? (null as T) : res.json();
}

/** SWR hook for GET endpoints (path without the /api prefix). Pass `null` to skip the request. */
export function useApi<T>(path: string | null, config?: SWRConfiguration<T>) {
  return useSWR<T>(path, fetcher, { revalidateOnFocus: false, ...config });
}
