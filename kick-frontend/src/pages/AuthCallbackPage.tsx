import { useEffect, useState } from "react";
import { Zap } from "lucide-react";

interface AuthCallbackPageProps {
  onComplete: () => void;
}

export function AuthCallbackPage({ onComplete }: AuthCallbackPageProps) {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");
    const sessionId = params.get("session_id");

    // Case 1: Redirected back from backend with session_id
    if (sessionId) {
      localStorage.setItem("kick_session_id", sessionId);
      // Clean URL and reload to trigger auth check
      window.history.replaceState({}, document.title, "/");
      onComplete();
      return;
    }

    // Case 2: Direct OAuth callback with code + state (backend handles exchange)
    if (code && state) {
      // Redirect to backend callback endpoint which will exchange the code
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      window.location.href = `${apiUrl}/api/auth/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`;
      return;
    }

    setError("Invalid callback — missing authorization code.");
  }, [onComplete]);

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <div className="text-center">
          <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-red-500/20 mx-auto mb-4">
            <Zap className="w-9 h-9 text-red-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Authentication Failed</h2>
          <p className="text-sm text-zinc-400 mb-4">{error}</p>
          <button
            onClick={() => {
              window.history.replaceState({}, document.title, "/");
              window.location.reload();
            }}
            className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-black font-medium rounded-lg text-sm transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-zinc-950">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-zinc-400">Connecting to Kick...</p>
      </div>
    </div>
  );
}
