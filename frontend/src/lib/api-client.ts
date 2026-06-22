import { signOut } from "next-auth/react";
import type { Session } from "next-auth";

// Custom error classes
export class ProError extends Error {
  constructor(message = "Pro subscription required") {
    super(message);
    this.name = "ProError";
  }
}

export class ServiceError extends Error {
  constructor(
    message = "Service temporarily unavailable",
    public readonly status?: number
  ) {
    super(message);
    this.name = "ServiceError";
  }
}

/**
 * Resolve the backend base URL from environment variables.
 * NEXT_PUBLIC_BACKEND_URL is available on the client side;
 * BACKEND_URL is available on the server side (SSR/RSC).
 */
function getBackendUrl(): string {
  if (typeof window === "undefined") {
    return (
      process.env.BACKEND_URL ||
      process.env.NEXT_PUBLIC_BACKEND_URL ||
      "http://localhost:8000"
    );
  }
  return (
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    "http://localhost:8000"
  );
}

/**
 * Build headers for a backend request. Attaches Authorization: Bearer
 * when a session with a backendToken is available.
 */
function buildHeaders(session: Session | null | undefined, extra: Record<string, string> = {}): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...extra,
  };

  if (session?.backendToken) {
    headers["Authorization"] = `Bearer ${session.backendToken}`;
  }

  return headers;
}

/**
 * Handle non-OK responses by throwing typed errors or signing out on 401.
 */
async function handleResponseError(res: Response): Promise<never> {
  if (res.status === 401) {
    // Token expired or invalid — sign out and redirect to login
    if (typeof window !== "undefined") {
      await signOut({ callbackUrl: "/login" });
    }
    throw new ServiceError("Unauthorized — please sign in again", 401);
  }

  // Note: all features are open to every tier, so a 403 is a genuine access
  // error (e.g. accessing another user's report). Surface the backend detail
  // via the generic handler below rather than a misleading "Pro required" message.

  if (res.status === 503 || res.status >= 500) {
    throw new ServiceError(
      `Service temporarily unavailable (HTTP ${res.status})`,
      res.status
    );
  }

  // Fallback: read error body if available
  let detail = `HTTP ${res.status}`;
  try {
    const body = await res.json();
    detail = body?.detail ?? body?.message ?? detail;
  } catch {
    // Ignore JSON parse failures
  }
  throw new ServiceError(detail, res.status);
}

/**
 * Typed GET request to the FastAPI backend.
 *
 * @param path - API path, e.g. "/reports/123"
 * @param session - NextAuth session object (can be null for unauthenticated endpoints)
 * @returns Parsed JSON response typed as T
 */
export async function apiGet<T>(path: string, session?: Session | null): Promise<T> {
  const url = `${getBackendUrl()}${path}`;
  const res = await fetch(url, {
    method: "GET",
    headers: buildHeaders(session),
    cache: "no-store",
  });

  if (!res.ok) {
    await handleResponseError(res);
  }

  return res.json() as Promise<T>;
}

/**
 * Typed POST request to the FastAPI backend.
 *
 * @param path - API path, e.g. "/reports"
 * @param body - Request body, will be JSON-serialized
 * @param session - NextAuth session object
 * @returns Parsed JSON response typed as T
 */
export async function apiPost<T, B>(path: string, body: B, session?: Session | null): Promise<T> {
  const url = `${getBackendUrl()}${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: buildHeaders(session),
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    await handleResponseError(res);
  }

  return res.json() as Promise<T>;
}

/**
 * Typed DELETE request to the FastAPI backend.
 *
 * @param path - API path, e.g. "/reports/123"
 * @param session - NextAuth session object
 */
export async function apiDelete(path: string, session?: Session | null): Promise<void> {
  const url = `${getBackendUrl()}${path}`;
  const res = await fetch(url, {
    method: "DELETE",
    headers: buildHeaders(session),
  });

  if (!res.ok) {
    await handleResponseError(res);
  }
}
