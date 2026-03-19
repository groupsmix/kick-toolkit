const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getAuthHeaders(): Record<string, string> {
  const sessionId = localStorage.getItem("kick_session_id");
  if (sessionId) {
    return { Authorization: `Bearer ${sessionId}` };
  }
  return {};
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    let detail = `API error: ${res.status}`;
    try {
      const parsed = JSON.parse(body);
      if (parsed.detail) detail = parsed.detail;
    } catch {
      // use default message
    }
    throw new Error(detail);
  }
  return res.json();
}

export function useApiUrl() {
  return API_URL;
}
