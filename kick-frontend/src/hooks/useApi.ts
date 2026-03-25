const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function api<T>(path: string, options?: RequestInit, _retryCount = 0): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  // Handle rate limiting with automatic retry
  if (res.status === 429 && _retryCount < 3) {
    const retryAfter = parseInt(res.headers.get("Retry-After") || "0", 10);
    const delayMs = retryAfter > 0 ? retryAfter * 1000 : Math.min(1000 * 2 ** _retryCount, 8000);
    await new Promise((resolve) => setTimeout(resolve, delayMs));
    return api<T>(path, options, _retryCount + 1);
  }

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    let detail = `API error: ${res.status}`;
    if (res.status === 429) {
      detail = "Too many requests. Please slow down and try again in a moment.";
    } else {
      try {
        const parsed = JSON.parse(body);
        if (parsed.detail) detail = parsed.detail;
      } catch {
        // use default message
      }
    }
    throw new Error(detail);
  }
  return res.json();
}

export function useApiUrl() {
  return API_URL;
}
