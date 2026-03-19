import { useAuth } from "@/hooks/useAuth";
import { Zap, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

export function LoginPage() {
  const { login } = useAuth();

  return (
    <div className="flex items-center justify-center min-h-screen bg-zinc-950">
      <div className="w-full max-w-md mx-auto px-6">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-emerald-500 mx-auto mb-4">
            <Zap className="w-9 h-9 text-black" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">KickTools</h1>
          <p className="text-zinc-500 mt-2 text-sm uppercase tracking-widest">Streamer Toolkit</p>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-8">
          <h2 className="text-xl font-semibold text-white text-center mb-2">
            Welcome back
          </h2>
          <p className="text-sm text-zinc-400 text-center mb-6">
            Connect your Kick account to access your dashboard, chat bot, giveaways, and more.
          </p>

          <Button
            onClick={login}
            className="w-full py-6 bg-emerald-500 hover:bg-emerald-600 text-black font-bold text-base rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <ExternalLink className="w-5 h-5" />
            Connect with Kick
          </Button>

          <p className="text-xs text-zinc-600 text-center mt-4">
            You'll be redirected to Kick to authorize access.
          </p>
        </div>

        <p className="text-xs text-zinc-700 text-center mt-6">
          By connecting, you agree to let KickTools access your Kick channel data.
        </p>
      </div>
    </div>
  );
}
