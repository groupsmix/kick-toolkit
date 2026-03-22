import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Clock, Bot, Gift, Shield, Trophy, Settings, Download, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/layout/Header";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";

interface ActivityEntry {
  id: string;
  channel: string;
  action: string;
  detail: string;
  created_at: string;
}

const actionIcons: Record<string, React.ElementType> = {
  bot: Bot,
  giveaway: Gift,
  moderation: Shield,
  tournament: Trophy,
  settings: Settings,
};

const actionColors: Record<string, string> = {
  bot: "text-cyan-400 bg-cyan-400/10",
  giveaway: "text-emerald-400 bg-emerald-400/10",
  moderation: "text-red-400 bg-red-400/10",
  tournament: "text-amber-400 bg-amber-400/10",
  settings: "text-blue-400 bg-blue-400/10",
};

function getActionCategory(action: string): string {
  if (action.includes("bot") || action.includes("command")) return "bot";
  if (action.includes("giveaway")) return "giveaway";
  if (action.includes("mod") || action.includes("ban") || action.includes("timeout")) return "moderation";
  if (action.includes("tournament")) return "tournament";
  return "settings";
}

function formatTimeAgo(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(ts).toLocaleDateString();
}

// Demo entries for when the API returns empty
const demoEntries: ActivityEntry[] = [
  { id: "demo-1", channel: "demo", action: "bot_command_created", detail: "Created command !socials", created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: "demo-2", channel: "demo", action: "giveaway_started", detail: "Started giveaway: Steam Gift Card", created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: "demo-3", channel: "demo", action: "moderation_action", detail: "Auto-banned spam_bot_99 for link spam", created_at: new Date(Date.now() - 10800000).toISOString() },
  { id: "demo-4", channel: "demo", action: "settings_updated", detail: "Updated bot prefix to !", created_at: new Date(Date.now() - 14400000).toISOString() },
  { id: "demo-5", channel: "demo", action: "giveaway_completed", detail: "Giveaway ended: viewer_jenny won Steam Gift Card", created_at: new Date(Date.now() - 18000000).toISOString() },
  { id: "demo-6", channel: "demo", action: "tournament_created", detail: "Created tournament: Friday Night Fights", created_at: new Date(Date.now() - 21600000).toISOString() },
];

export function ActivityPage() {
  const { user } = useAuth();
  const [filter, setFilter] = useState<string>("all");

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["activity"],
    queryFn: () => api<{ entries: ActivityEntry[] }>("/api/activity?limit=100"),
  });

  const entries = data?.entries && data.entries.length > 0 ? data.entries : demoEntries;

  const filtered = filter === "all"
    ? entries
    : entries.filter((e) => getActionCategory(e.action) === filter);

  const exportCSV = () => {
    if (filtered.length === 0) {
      toast.error("No entries to export");
      return;
    }
    const headers = ["timestamp", "action", "detail"];
    const rows = filtered.map((e) => [
      e.created_at,
      e.action,
      `"${e.detail.replace(/"/g, '""')}"`,
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `activity-log-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Exported ${filtered.length} entries`);
  };

  const filters = [
    { key: "all", label: "All" },
    { key: "bot", label: "Bot" },
    { key: "giveaway", label: "Giveaways" },
    { key: "moderation", label: "Moderation" },
    { key: "tournament", label: "Tournaments" },
    { key: "settings", label: "Settings" },
  ];

  return (
    <>
      <Header title="Activity Log" subtitle="Track all actions and events" user={user} />
      <div className="p-4 sm:p-6 space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex flex-wrap gap-2">
            {filters.map((f) => (
              <Button
                key={f.key}
                variant={filter === f.key ? "default" : "outline"}
                size="sm"
                onClick={() => setFilter(f.key)}
                className={filter === f.key
                  ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                  : "border-zinc-700 text-zinc-400 hover:text-white"
                }
              >
                {f.label}
              </Button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="border-zinc-700 text-zinc-400 hover:text-white"
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={exportCSV}
              className="border-zinc-700 text-zinc-400 hover:text-white"
            >
              <Download className="w-4 h-4 mr-1" />
              CSV
            </Button>
          </div>
        </div>

        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-emerald-400" />
              Recent Activity
              <span className="text-sm font-normal text-zinc-500">({filtered.length} entries)</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 bg-zinc-800/50 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : filtered.length === 0 ? (
              <div className="text-center py-8">
                <Clock className="w-10 h-10 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500 text-sm">No activity entries found</p>
              </div>
            ) : (
              <div className="space-y-1">
                {filtered.map((entry) => {
                  const category = getActionCategory(entry.action);
                  const Icon = actionIcons[category] || Clock;
                  const colorClass = actionColors[category] || "text-zinc-400 bg-zinc-400/10";
                  const [textColor, bgColor] = colorClass.split(" ");
                  return (
                    <div
                      key={entry.id}
                      className="flex items-start gap-3 p-3 rounded-lg hover:bg-zinc-800/30 transition-colors"
                    >
                      <div className={`p-2 rounded-lg ${bgColor} flex-shrink-0`}>
                        <Icon className={`w-4 h-4 ${textColor}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white">{entry.detail || entry.action}</p>
                        <p className="text-xs text-zinc-500 mt-0.5">{entry.action.replace(/_/g, " ")}</p>
                      </div>
                      <span className="text-xs text-zinc-600 flex-shrink-0 whitespace-nowrap">
                        {formatTimeAgo(entry.created_at)}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
