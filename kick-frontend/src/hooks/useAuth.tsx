import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { api } from "@/hooks/useApi";

interface KickUser {
  user_id?: number;
  name?: string;
  email?: string;
  profile_picture?: string;
  [key: string]: unknown;
}

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

  const sessionId = localStorage.getItem("kick_session_id");

  // Check existing session on mount
  useEffect(() => {
    if (!sessionId) {
      setLoading(false);
      return;
    }

    api<{ user: KickUser }>(`/api/auth/me?session_id=${sessionId}`)
      .then((data) => {
        setUser(data.user);
      })
      .catch(() => {
        localStorage.removeItem("kick_session_id");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, [sessionId]);

  const login = useCallback(async () => {
    const data = await api<{ auth_url: string; session_id: string }>("/api/auth/login");
    // Store session_id for later
    localStorage.setItem("kick_session_id", data.session_id);
    // Redirect to Kick OAuth
    window.location.href = data.auth_url;
  }, []);

  const logout = useCallback(async () => {
    if (sessionId) {
      try {
        await api(`/api/auth/logout?session_id=${sessionId}`, { method: "POST" });
      } catch {
        // Ignore errors during logout
      }
    }
    localStorage.removeItem("kick_session_id");
    setUser(null);
  }, [sessionId]);

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
