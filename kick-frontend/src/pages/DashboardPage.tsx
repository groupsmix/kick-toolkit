import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  MessageSquare,
  ShieldAlert,
  Users,
  Gift,
  Trophy,
  Bot,
  TrendingUp,
  Activity,
} from "lucide-react";

interface DashboardStats {
  total_messages: number;
  flagged_messages: number;
  unique_users: number;
  active_giveaways: number;
  active_tournaments: number;
  flagged_accounts: number;
  total_commands: number;
  moderation_rate: number;
}

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = () => {
    setLoading(true);
    setError(null);
    api<DashboardStats>("/api/dashboard/stats")
      .then(setStats)
      .catch((err) => {
        setError(err.message || "Failed to load dashboard stats");
        toast.error("Failed to load dashboard stats");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-zinc-400">{error || "Failed to load data"}</p>
        <Button onClick={fetchStats} variant="outline" className="border-zinc-700 text-zinc-300">
          Retry
        </Button>
      </div>
    );
  }

  const statCards = [
    {
      title: "Total Messages",
      value: stats.total_messages.toLocaleString(),
      icon: MessageSquare,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      change: "+12%",
    },
    {
      title: "Unique Chatters",
      value: stats.unique_users.toLocaleString(),
      icon: Users,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      change: "+5%",
    },
    {
      title: "Flagged Messages",
      value: stats.flagged_messages.toLocaleString(),
      icon: ShieldAlert,
      color: "text-red-400",
      bg: "bg-red-500/10",
      change: `-${stats.moderation_rate}%`,
    },
    {
      title: "Active Giveaways",
      value: stats.active_giveaways.toString(),
      icon: Gift,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      change: "Live",
    },
    {
      title: "Active Tournaments",
      value: stats.active_tournaments.toString(),
      icon: Trophy,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      change: "In Progress",
    },
    {
      title: "Flagged Accounts",
      value: stats.flagged_accounts.toString(),
      icon: ShieldAlert,
      color: "text-orange-400",
      bg: "bg-orange-500/10",
      change: "Watching",
    },
    {
      title: "Bot Commands",
      value: stats.total_commands.toString(),
      icon: Bot,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
      change: "Active",
    },
    {
      title: "Mod Rate",
      value: `${stats.moderation_rate}%`,
      icon: Activity,
      color: "text-pink-400",
      bg: "bg-pink-500/10",
      change: "Auto",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-emerald-500/20 via-emerald-500/10 to-transparent border border-emerald-500/20 p-6">
        <div className="relative z-10">
          <h2 className="text-2xl font-bold text-white mb-1">Welcome back, Streamer!</h2>
          <p className="text-zinc-400">
            Your toolkit is running smoothly. Here's what's happening on your channel.
          </p>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <TrendingUp className="w-32 h-32 text-emerald-500" />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title} className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs text-zinc-500 uppercase tracking-wider">{stat.title}</p>
                    <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                  </div>
                  <div className={`p-2 rounded-lg ${stat.bg}`}>
                    <Icon className={`w-5 h-5 ${stat.color}`} />
                  </div>
                </div>
                <Badge variant="outline" className="mt-3 text-[10px] border-zinc-700 text-zinc-400">
                  {stat.change}
                </Badge>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <Gift className="w-4 h-4 text-emerald-400" />
              Quick Giveaway
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-zinc-500 mb-3">Start a quick giveaway with one click</p>
            <button className="w-full px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-black font-medium rounded-lg text-sm transition-colors">
              Start Giveaway
            </button>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <Trophy className="w-4 h-4 text-amber-400" />
              Quick Tournament
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-zinc-500 mb-3">Open registration for a new tournament</p>
            <button className="w-full px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black font-medium rounded-lg text-sm transition-colors">
              Create Tournament
            </button>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-400" />
              Security Check
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-zinc-500 mb-3">Scan recent chatters for alt accounts</p>
            <button className="w-full px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 font-medium rounded-lg text-sm transition-colors border border-red-500/20">
              Run Scan
            </button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
