import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  Line,
  LineChart,
} from "recharts";
import {
  Eye,
  Users,
  TrendingUp,
  Clock,
  Activity,
  BarChart3,
  RefreshCw,
} from "lucide-react";

interface ViewerTimeline {
  timestamp: string;
  viewer_count: number;
  chatter_count: number;
}

interface StreamSession {
  started_at: string;
  ended_at: string | null;
  peak_viewers: number;
  avg_viewers: number;
  duration_minutes: number;
  title: string;
  game: string;
}

interface ViewerCountData {
  channel: string;
  period: string;
  viewer_timeline: ViewerTimeline[];
  sessions: StreamSession[];
  stats: {
    all_time_peak: number;
    avg_viewers: number;
    total_hours_streamed: number;
  };
}

export function ViewerCountPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [data, setData] = useState<ViewerCountData | null>(null);
  const [period, setPeriod] = useState<"day" | "week" | "month">("week");
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api<ViewerCountData>(
        `/api/analytics/viewercount/${channel}?period=${period}`
      );
      setData(result);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load viewer data");
    } finally {
      setLoading(false);
    }
  }, [channel, period]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  const formatNumber = (n: number) => {
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
    return n.toFixed(0);
  };

  const formatTime = (ts: string) => {
    const d = new Date(ts);
    if (period === "day") return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit" });
  };

  const formatDate = (ts: string) =>
    new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });

  const formatDuration = (minutes: number) => {
    const h = Math.floor(minutes / 60);
    const m = Math.round(minutes % 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const chartData = data?.viewer_timeline.map((t) => ({
    time: formatTime(t.timestamp),
    viewers: t.viewer_count,
    chatters: t.chatter_count,
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-blue-500/20 via-cyan-500/10 to-transparent border border-blue-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Eye className="w-6 h-6 text-blue-400" />
              <h2 className="text-2xl font-bold text-white">Viewer Count Tracker</h2>
              <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-[10px] uppercase font-bold">
                Premium
              </Badge>
            </div>
            <p className="text-zinc-400">
              Track viewer counts over time with historical graphs and session analytics.
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-blue-400 hover:text-blue-300"
            onClick={fetchData}
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </Button>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <Eye className="w-32 h-32 text-blue-500" />
        </div>
      </div>

      {/* Period Selector */}
      <div className="flex items-center gap-2">
        {(["day", "week", "month"] as const).map((p) => (
          <Button
            key={p}
            variant={period === p ? "default" : "ghost"}
            size="sm"
            className={period === p ? "bg-blue-500 hover:bg-blue-600 text-white" : "text-zinc-400"}
            onClick={() => setPeriod(p)}
          >
            {p === "day" ? "24h" : p === "week" ? "7 Days" : "30 Days"}
          </Button>
        ))}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <TrendingUp className="w-5 h-5 text-emerald-400 mb-2" />
            <p className="text-2xl font-bold text-white">
              {formatNumber(data?.stats.all_time_peak || 0)}
            </p>
            <p className="text-[10px] text-zinc-500 uppercase">All-Time Peak</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <Eye className="w-5 h-5 text-blue-400 mb-2" />
            <p className="text-2xl font-bold text-white">
              {formatNumber(data?.stats.avg_viewers || 0)}
            </p>
            <p className="text-[10px] text-zinc-500 uppercase">Avg Viewers</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <Clock className="w-5 h-5 text-amber-400 mb-2" />
            <p className="text-2xl font-bold text-white">
              {data?.stats.total_hours_streamed.toFixed(1) || 0}h
            </p>
            <p className="text-[10px] text-zinc-500 uppercase">Total Hours</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <Activity className="w-5 h-5 text-purple-400 mb-2" />
            <p className="text-2xl font-bold text-white">
              {data?.sessions.length || 0}
            </p>
            <p className="text-[10px] text-zinc-500 uppercase">Recent Sessions</p>
          </CardContent>
        </Card>
      </div>

      {/* Viewer Count Chart */}
      {chartData.length > 0 ? (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" />
              Viewer Count Over Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="viewerCountGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="chatterCountGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis
                  dataKey="time"
                  tick={{ fill: "#71717a", fontSize: 10 }}
                  interval="preserveStartEnd"
                />
                <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: "#18181b",
                    border: "1px solid #27272a",
                    borderRadius: 8,
                  }}
                  labelStyle={{ color: "#a1a1aa" }}
                />
                <Area
                  type="monotone"
                  dataKey="viewers"
                  stroke="#3b82f6"
                  fill="url(#viewerCountGrad)"
                  strokeWidth={2}
                  name="Viewers"
                />
                <Area
                  type="monotone"
                  dataKey="chatters"
                  stroke="#8b5cf6"
                  fill="url(#chatterCountGrad)"
                  strokeWidth={1.5}
                  name="Chatters"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      ) : (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-8 text-center">
            <Eye className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
            <p className="text-zinc-400 text-sm">No viewer data for this period</p>
            <p className="text-zinc-600 text-xs mt-1">
              Data will appear once stream monitoring begins
            </p>
          </CardContent>
        </Card>
      )}

      {/* Recent Sessions */}
      {data?.sessions && data.sessions.length > 0 && (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-400" />
              Recent Stream Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.sessions.map((session, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/30 border border-zinc-800/50"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {session.title || "Untitled Stream"}
                    </p>
                    <div className="flex items-center gap-3 text-[11px] text-zinc-500 mt-1">
                      <span>{formatDate(session.started_at)}</span>
                      {session.game && <span className="text-zinc-600">{session.game}</span>}
                      <span>{formatDuration(session.duration_minutes)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 ml-4">
                    <div className="text-right">
                      <p className="text-sm font-bold text-white">{formatNumber(session.peak_viewers)}</p>
                      <p className="text-[10px] text-zinc-500">Peak</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-blue-400">{formatNumber(session.avg_viewers)}</p>
                      <p className="text-[10px] text-zinc-500">Avg</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Session Comparison Chart */}
      {data?.sessions && data.sessions.length > 1 && (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <Users className="w-4 h-4 text-emerald-400" />
              Session Peak vs Average Viewers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart
                data={[...data.sessions].reverse().map((s, i) => ({
                  session: `#${i + 1}`,
                  peak: s.peak_viewers,
                  avg: Math.round(s.avg_viewers),
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="session" tick={{ fill: "#71717a", fontSize: 11 }} />
                <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: "#18181b",
                    border: "1px solid #27272a",
                    borderRadius: 8,
                  }}
                  labelStyle={{ color: "#a1a1aa" }}
                />
                <Line type="monotone" dataKey="peak" stroke="#10b981" strokeWidth={2} name="Peak" dot={{ fill: "#10b981" }} />
                <Line type="monotone" dataKey="avg" stroke="#3b82f6" strokeWidth={2} name="Avg" dot={{ fill: "#3b82f6" }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
