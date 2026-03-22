import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  Search,
  AlertTriangle,
  MessageSquare,
  User,
  Clock,
  BarChart3,
  Download,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface ChatLog {
  id: string;
  channel: string;
  username: string;
  message: string;
  timestamp: string;
  flagged: boolean;
  flag_reason: string | null;
}

interface ChatStats {
  channel: string;
  total_messages: number;
  flagged_messages: number;
  unique_users: number;
  top_chatters: { username: string; count: number }[];
}

export function ChatLogsPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [logs, setLogs] = useState<ChatLog[]>([]);
  const [stats, setStats] = useState<ChatStats | null>(null);
  const [search, setSearch] = useState("");
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    try {
      const params = new URLSearchParams({ channel });
      if (search) params.set("search", search);
      if (flaggedOnly) params.set("flagged_only", "true");
      if (selectedUser) params.set("username", selectedUser);

      const data = await api<{ logs: ChatLog[]; total: number }>(`/api/chatlogs?${params}`);
      setLogs(data.logs);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load chat logs";
      setError(msg);
      toast.error(msg);
    }
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchLogs(),
      api<ChatStats>(`/api/chatlogs/stats/${channel}`).then(setStats),
    ])
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [channel]);

  useEffect(() => {
    fetchLogs();
  }, [search, flaggedOnly, selectedUser]);

  const formatTime = (ts: string) => {
    const date = new Date(ts);
    return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
  };

  const exportCSV = () => {
    if (logs.length === 0) {
      toast.error("No logs to export");
      return;
    }
    const headers = ["timestamp", "username", "message", "flagged", "flag_reason"];
    const rows = logs.map((log) => [
      log.timestamp,
      log.username,
      `"${log.message.replace(/"/g, '""')}"`,
      log.flagged ? "yes" : "no",
      log.flag_reason || "",
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `chat-logs-${channel}-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Exported ${logs.length} log entries`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error && logs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-zinc-400">{error}</p>
        <Button onClick={() => window.location.reload()} variant="outline" className="border-zinc-700 text-zinc-300">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 flex items-center gap-3">
              <MessageSquare className="w-8 h-8 text-blue-400" />
              <div>
                <p className="text-2xl font-bold text-white">{stats.total_messages}</p>
                <p className="text-xs text-zinc-500">Total Messages</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 flex items-center gap-3">
              <AlertTriangle className="w-8 h-8 text-red-400" />
              <div>
                <p className="text-2xl font-bold text-white">{stats.flagged_messages}</p>
                <p className="text-xs text-zinc-500">Flagged</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 flex items-center gap-3">
              <User className="w-8 h-8 text-purple-400" />
              <div>
                <p className="text-2xl font-bold text-white">{stats.unique_users}</p>
                <p className="text-xs text-zinc-500">Unique Users</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 flex items-center gap-3">
              <BarChart3 className="w-8 h-8 text-emerald-400" />
              <div>
                <p className="text-2xl font-bold text-white">
                  {stats.total_messages > 0
                    ? ((stats.flagged_messages / stats.total_messages) * 100).toFixed(1)
                    : 0}%
                </p>
                <p className="text-xs text-zinc-500">Flag Rate</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Chat Logs */}
        <div className="lg:col-span-3 space-y-4">
          {/* Filters */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search messages or usernames..."
                    className="pl-9 bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={flaggedOnly} onCheckedChange={setFlaggedOnly} />
                  <Label className="text-zinc-400 text-sm whitespace-nowrap">Flagged Only</Label>
                </div>
                {selectedUser && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedUser(null)}
                    className="text-zinc-400"
                  >
                    Clear Filter: {selectedUser}
                  </Button>
                )}
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
            </CardContent>
          </Card>

          {/* Log Entries */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-zinc-400">{total} messages</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[500px]">
                <div className="divide-y divide-zinc-800/50">
                  {logs.map((log) => (
                    <div
                      key={log.id}
                      className={`px-4 py-3 hover:bg-zinc-800/30 transition-colors ${
                        log.flagged ? "border-l-2 border-l-red-500" : ""
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setSelectedUser(log.username)}
                              className="text-sm font-medium text-emerald-400 hover:text-emerald-300 hover:underline"
                            >
                              {log.username}
                            </button>
                            <span className="text-xs text-zinc-600 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {formatTime(log.timestamp)}
                            </span>
                            {log.flagged && (
                              <Badge className="text-[10px] bg-red-500/10 text-red-400 border-red-500/20">
                                <AlertTriangle className="w-3 h-3 mr-1" />
                                Flagged
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-zinc-300 mt-1">{log.message}</p>
                          {log.flag_reason && (
                            <p className="text-xs text-red-400/70 mt-1">{log.flag_reason}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Top Chatters Sidebar */}
        <div className="space-y-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-emerald-400" />
                Top Chatters
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0 space-y-2">
              {stats?.top_chatters.map((chatter, i) => (
                <button
                  key={chatter.username}
                  onClick={() => setSelectedUser(chatter.username)}
                  className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-zinc-800/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold w-5 ${i < 3 ? "text-amber-400" : "text-zinc-500"}`}>
                      #{i + 1}
                    </span>
                    <span className="text-sm text-white">{chatter.username}</span>
                  </div>
                  <Badge variant="outline" className="text-[10px] border-zinc-700 text-zinc-400">
                    {chatter.count} msgs
                  </Badge>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
