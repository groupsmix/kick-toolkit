import { createContext, useContext, useState, useEffect, useCallback, useRef, type ReactNode } from "react";
import { api } from "@/hooks/useApi";
import type { KickUser } from "@/types";

interface AuthContextType {
  user: KickUser | null;
  loading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => {},
  logout: async () => {},
  isAuthenticated: false,
});

/** Refresh the access token 5 minutes before it expires. */
const REFRESH_MARGIN_MS = 5 * 60 * 1000;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<KickUser | null>(null);
  const [loading, setLoading] = useState(true);
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearRefreshTimer = useCallback(() => {
    if (refreshTimer.current) {
      clearTimeout(refreshTimer.current);
      refreshTimer.current = null;
    }
  }, []);

  const scheduleRefresh = useCallback(
    (expiresInSeconds?: number) => {
      clearRefreshTimer();
      if (!expiresInSeconds || expiresInSeconds <= 0) return;

      const delayMs = Math.max(expiresInSeconds * 1000 - REFRESH_MARGIN_MS, 0);

      refreshTimer.current = setTimeout(async () => {
        try {
          const result = await api<{ status: string; expires_in?: number }>(
            "/api/auth/refresh",
            { method: "POST" },
          );
          if (result.expires_in) {
            scheduleRefresh(result.expires_in);
          }
        } catch {
          // Refresh failed — user will be prompted to re-authenticate on next API call
        }
      }, delayMs);
    },
    [clearRefreshTimer],
  );

  // Validate session on mount — skip on the OAuth callback page to avoid
  // a race condition where we'd call /api/auth/me before the token exchange
  // has completed, get a 401, and clear the session_id from localStorage.
  useEffect(() => {
    if (window.location.pathname === "/auth/callback") {
      setLoading(false);
      return;
    }

    const sessionId = localStorage.getItem("kick_session_id");
    if (!sessionId) {
      setLoading(false);
      return;
    }

    api<{ user: KickUser; expires_in?: number }>("/api/auth/me")
      .then((data) => {
        setUser(data.user);
        if (data.expires_in) {
          scheduleRefresh(data.expires_in);
        }
      })
      .catch(() => {
        localStorage.removeItem("kick_session_id");
        setUser(null);
      })
      .finally(() => setLoading(false));

    return () => clearRefreshTimer();
  }, [scheduleRefresh, clearRefreshTimer]);

  const login = useCallback(async () => {
    const data = await api<{ auth_url: string; session_id: string }>("/api/auth/login");
    localStorage.setItem("kick_session_id", data.session_id);
    window.location.href = data.auth_url;
  }, []);

  const logout = useCallback(async () => {
    clearRefreshTimer();
    const sessionId = localStorage.getItem("kick_session_id");
    if (sessionId) {
      try {
        await api("/api/auth/logout", { method: "POST" });
      } catch {
        // Ignore errors during logout
      }
    }
    localStorage.removeItem("kick_session_id");
    setUser(null);
  }, [clearRefreshTimer]);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
