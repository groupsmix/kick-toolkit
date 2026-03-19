import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<KickUser | null>(null);
  const [loading, setLoading] = useState(true);

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

    api<{ user: KickUser }>("/api/auth/me")
      .then((data) => {
        setUser(data.user);
      })
      .catch(() => {
        localStorage.removeItem("kick_session_id");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async () => {
    const data = await api<{ auth_url: string; session_id: string }>("/api/auth/login");
    localStorage.setItem("kick_session_id", data.session_id);
    window.location.href = data.auth_url;
  }, []);

  const logout = useCallback(async () => {
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
  }, []);

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
