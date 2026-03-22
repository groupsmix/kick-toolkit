import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { api } from "@/hooks/useApi";
import type { DashboardStats, SubscriptionResponse } from "@/types";
import {
  MessageSquare,
  ShieldAlert,
  Users,
  Gift,
  Trophy,
  Bot,
  TrendingUp,
  Activity,
  Crown,
  ArrowUpRight,
  CheckCircle2,
  Circle,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useState, useEffect } from "react";

interface OnboardingStep {
  id: string;
  label: string;
  description: string;
  path: string;
  check: (stats: DashboardStats) => boolean;
}

const onboardingSteps: OnboardingStep[] = [
  {
    id: "bot",
    label: "Set up your first bot command",
    description: "Create a custom chat command for your viewers",
    path: "/bot",
    check: (stats) => stats.total_commands > 0,
  },
  {
    id: "giveaway",
    label: "Create a giveaway",
    description: "Run your first giveaway to engage your audience",
    path: "/giveaway",
    check: (stats) => stats.active_giveaways > 0,
  },
  {
    id: "moderation",
    label: "Review moderation settings",
    description: "Configure AI moderation to keep your chat clean",
    path: "/bot",
    check: (stats) => stats.moderation_rate > 0,
  },
];

export function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [onboardingDismissed, setOnboardingDismissed] = useState(() =>
    localStorage.getItem("onboarding_dismissed") === "true"
  );

  const { data: stats, isLoading, error, refetch } = useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: () => api<DashboardStats>("/api/dashboard/stats"),
    refetchInterval: 30_000,
  });

  const { data: subData } = useQuery<SubscriptionResponse>({
    queryKey: ["subscription"],
    queryFn: () => api<SubscriptionResponse>("/api/subscription/me"),
  });

  const currentPlan = subData?.plan?.name || "Free";
  const planId = subData?.plan?.id || "free";
  const planLimits = subData?.plan?.limits || {};
  const usage = subData?.usage || {};

  const completedSteps = stats
    ? onboardingSteps.filter((step) => step.check(stats)).length
    : 0;
  const allStepsComplete = completedSteps === onboardingSteps.length;

  useEffect(() => {
    if (allStepsComplete && !onboardingDismissed) {
      const timer = setTimeout(() => {
        setOnboardingDismissed(true);
        localStorage.setItem("onboarding_dismissed", "true");
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [allStepsComplete, onboardingDismissed]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-zinc-400">{error instanceof Error ? error.message : "Failed to load data"}</p>
        <Button onClick={() => refetch()} variant="outline" className="border-zinc-700 text-zinc-300">
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
      change: "All time",
    },
    {
      title: "Unique Chatters",
      value: stats.unique_users.toLocaleString(),
      icon: Users,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      change: "All time",
    },
    {
      title: "Flagged Messages",
      value: stats.flagged_messages.toLocaleString(),
      icon: ShieldAlert,
      color: "text-red-400",
      bg: "bg-red-500/10",
      change: `${stats.moderation_rate}% rate`,
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
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">Welcome back, {user?.name || "Streamer"}!</h2>
            <p className="text-zinc-400">
              Your toolkit is running smoothly. Here's what's happening on your channel.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge
              className={`px-3 py-1 text-xs font-bold uppercase tracking-wider ${
                planId === "premium"
                  ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                  : planId === "pro"
                  ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                  : "bg-zinc-700/50 text-zinc-400 border-zinc-600/30"
              }`}
            >
              <Crown className="w-3 h-3 mr-1" />
              {currentPlan}
            </Badge>
            {planId === "free" && (
              <Button
                size="sm"
                className="bg-emerald-500 hover:bg-emerald-600 text-black text-xs font-semibold"
                onClick={() => navigate("/pricing")}
              >
                Upgrade
                <ArrowUpRight className="w-3 h-3 ml-1" />
              </Button>
            )}
          </div>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <TrendingUp className="w-32 h-32 text-emerald-500" />
        </div>
      </div>

      {/* Onboarding Checklist */}
      {!onboardingDismissed && stats && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-white flex items-center justify-between">
              <span className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Getting Started &mdash; {completedSteps}/{onboardingSteps.length} complete
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="text-zinc-500 hover:text-zinc-300 text-xs"
                onClick={() => {
                  setOnboardingDismissed(true);
                  localStorage.setItem("onboarding_dismissed", "true");
                }}
              >
                Dismiss
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {onboardingSteps.map((step) => {
                const done = step.check(stats);
                return (
                  <button
                    key={step.id}
                    onClick={() => !done && navigate(step.path)}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors ${
                      done
                        ? "bg-emerald-500/5 border border-emerald-500/10"
                        : "bg-zinc-800/50 border border-zinc-700/50 hover:border-emerald-500/30 cursor-pointer"
                    }`}
                  >
                    {done ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    ) : (
                      <Circle className="w-5 h-5 text-zinc-600 flex-shrink-0" />
                    )}
                    <div>
                      <p className={`text-sm font-medium ${done ? "text-emerald-400 line-through" : "text-white"}`}>
                        {step.label}
                      </p>
                      <p className="text-xs text-zinc-500">{step.description}</p>
                    </div>
                    {!done && (
                      <ArrowUpRight className="w-4 h-4 text-zinc-500 ml-auto flex-shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Usage Limits (for free plan) */}
      {planId === "free" && (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-400 flex items-center justify-between">
              <span>Plan Usage</span>
              <Button
                variant="ghost"
                size="sm"
                className="text-emerald-400 hover:text-emerald-300 text-xs"
                onClick={() => navigate("/pricing")}
              >
                Upgrade for unlimited
                <ArrowUpRight className="w-3 h-3 ml-1" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-zinc-500">Bot Commands</span>
                  <span className="text-xs text-zinc-400">
                    {usage.bot_commands || 0} / {planLimits.bot_commands === -1 ? "\u221E" : planLimits.bot_commands || 5}
                  </span>
                </div>
                <Progress
                  value={planLimits.bot_commands === -1 ? 0 : ((usage.bot_commands || 0) / (planLimits.bot_commands || 5)) * 100}
                  className="h-2"
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-zinc-500">Chat Logs</span>
                  <span className="text-xs text-zinc-400">
                    {usage.chat_log_entries || 0} / {planLimits.chat_log_entries === -1 ? "\u221E" : planLimits.chat_log_entries || 100}
                  </span>
                </div>
                <Progress
                  value={planLimits.chat_log_entries === -1 ? 0 : ((usage.chat_log_entries || 0) / (planLimits.chat_log_entries || 100)) * 100}
                  className="h-2"
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-zinc-500">Active Giveaways</span>
                  <span className="text-xs text-zinc-400">
                    {usage.active_giveaways || 0} / {planLimits.active_giveaways === -1 ? "\u221E" : planLimits.active_giveaways || 1}
                  </span>
                </div>
                <Progress
                  value={planLimits.active_giveaways === -1 ? 0 : ((usage.active_giveaways || 0) / (planLimits.active_giveaways || 1)) * 100}
                  className="h-2"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
                <p className="mt-3 text-[10px] text-zinc-500">
                  {stat.change}
                </p>
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
            <button
              onClick={() => navigate("/giveaway")}
              className="w-full px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-black font-medium rounded-lg text-sm transition-colors"
            >
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
            <button
              onClick={() => navigate("/tournament")}
              className="w-full px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black font-medium rounded-lg text-sm transition-colors"
            >
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
            <button
              onClick={() => navigate("/antialt")}
              className="w-full px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 font-medium rounded-lg text-sm transition-colors border border-red-500/20"
            >
              Run Scan
            </button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
