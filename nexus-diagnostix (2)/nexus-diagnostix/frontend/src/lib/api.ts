/**
 * Client HTTP de Nexus-Diagnostix.
 *
 * Thin wrapper autour de `fetch` qui :
 *  - injecte la base URL depuis `VITE_API_BASE_URL`,
 *  - sérialise le JSON,
 *  - injecte le JWT si présent,
 *  - normalise les erreurs RFC 7807.
 */

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string;
}

class ApiClientError extends Error {
  readonly status: number;
  readonly type: string;
  readonly detail: string;

  constructor(error: ApiError) {
    super(error.detail || error.title);
    this.name = "ApiClientError";
    this.status = error.status;
    this.type = error.type;
    this.detail = error.detail;
  }
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem("nexus_admin_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const init: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...getAuthHeader(),
    },
  };
  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  const response = await fetch(url, init);

  if (!response.ok) {
    let payload: ApiError;
    try {
      payload = (await response.json()) as ApiError;
    } catch {
      payload = {
        type: "network_error",
        title: "Erreur réseau",
        status: response.status,
        detail: response.statusText || "Une erreur réseau est survenue.",
      };
    }
    throw new ApiClientError(payload);
  }

  // 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
};

export { ApiClientError };
