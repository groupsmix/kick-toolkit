import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  Bar,
  BarChart,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Clock,
  Gamepad2,
  Users,
  MessageSquare,
  Star,
  Calendar,
  PlusCircle,
  Activity,
  Target,
} from "lucide-react";

interface StreamSession {
  id: string;
  channel: string;
  started_at: string;
  ended_at: string | null;
  duration_minutes: number;
  peak_viewers: number;
  avg_viewers: number;
  chat_messages: number;
  new_followers: number;
  new_subscribers: number;
  stream_score: number;
  game: string;
  title: string;
}

interface StreamScore {
  channel: string;
  overall_score: number;
  viewer_score: number;
  chat_score: number;
  growth_score: number;
  consistency_score: number;
  trend: string;
}

interface BestTimeSlot {
  day_of_week: number;
  hour: number;
  competition_score: number;
  recommended_score: number;
  avg_category_viewers: number;
  active_streamers: number;
}

interface GameRec {
  game: string;
  growth_potential: number;
  competition_level: string;
  avg_viewers_in_category: number;
  trending: boolean;
  reason: string;
}

interface Overview {
  channel: string;
  stream_score: StreamScore;
  recent_sessions: StreamSession[];
  best_times: BestTimeSlot[];
  game_recommendations: GameRec[];
  weekly_summary: {
    total_streams: number;
    avg_score: number;
    total_viewers: number;
    total_followers: number;
    total_messages: number;
  };
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const TREND_CONFIG: Record<string, { icon: typeof TrendingUp; color: string; bg: string; label: string }> = {
  rising: { icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-500/10", label: "Rising" },
  stable: { icon: Minus, color: "text-blue-400", bg: "bg-blue-500/10", label: "Stable" },
  declining: { icon: TrendingDown, color: "text-red-400", bg: "bg-red-500/10", label: "Declining" },
};

export function StreamIntelPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [overview, setOverview] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionForm, setSessionForm] = useState({
    duration_minutes: 0,
    peak_viewers: 0,
    avg_viewers: 0,
    chat_messages: 0,
    new_followers: 0,
    new_subscribers: 0,
    game: "",
    title: "",
  });

  const fetchData = useCallback(async () => {
    try {
      const data = await api<Overview>(`/api/stream-intel/overview/${channel}`);
      setOverview(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [channel]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  const recordSession = async () => {
    try {
      await api("/api/stream-intel/sessions", {
        method: "POST",
        body: JSON.stringify({ channel, ...sessionForm }),
      });
      toast.success("Stream session recorded!");
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to record session");
    }
  };

  const trendConfig = (trend: string) =>
    TREND_CONFIG[trend] || TREND_CONFIG.stable;

  const formatScore = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 60) return "text-blue-400";
    if (score >= 40) return "text-amber-400";
    return "text-red-400";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const chartData = overview?.recent_sessions
    ? [...overview.recent_sessions]
        .filter((s) => s.stream_score > 0)
        .reverse()
        .map((s) => ({
          date: new Date(s.started_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
          score: s.stream_score,
          viewers: s.avg_viewers,
          messages: s.chat_messages,
          game: s.game,
        }))
    : [];

  const bestTimesChart = overview?.best_times.map((t) => ({
    label: `${DAYS[t.day_of_week]} ${t.hour}:00`,
    score: t.recommended_score,
    competition: t.competition_score,
    viewers: t.avg_category_viewers,
  })) || [];

  const tc = overview ? trendConfig(overview.stream_score.trend) : TREND_CONFIG.stable;
  const TrendIcon = tc.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-emerald-500/20 via-cyan-500/10 to-transparent border border-emerald-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-6 h-6 text-emerald-400" />
              <h2 className="text-2xl font-bold text-white">Stream Intelligence</h2>
              <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px] uppercase font-bold">
                Pro
              </Badge>
            </div>
            <p className="text-zinc-400">
              Your stream performance at a glance. Stream scores, best times, and growth insights.
            </p>
          </div>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <Activity className="w-32 h-32 text-emerald-500" />
        </div>
      </div>

      {/* Score Cards */}
      {overview && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <Zap className="w-5 h-5 text-amber-400" />
                <Badge className={`${tc.bg} ${tc.color} text-[10px]`}>
                  <TrendIcon className="w-3 h-3 mr-1" />
                  {tc.label}
                </Badge>
              </div>
              <p className={`text-2xl font-bold ${formatScore(overview.stream_score.overall_score)}`}>
                {overview.stream_score.overall_score.toFixed(0)}
              </p>
              <p className="text-[10px] text-zinc-500 uppercase">Overall Score</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <Users className="w-5 h-5 text-blue-400 mb-2" />
              <p className="text-2xl font-bold text-white">
                {overview.stream_score.viewer_score.toFixed(0)}
              </p>
              <p className="text-[10px] text-zinc-500 uppercase">Viewer Score</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <MessageSquare className="w-5 h-5 text-purple-400 mb-2" />
              <p className="text-2xl font-bold text-white">
                {overview.stream_score.chat_score.toFixed(0)}
              </p>
              <p className="text-[10px] text-zinc-500 uppercase">Chat Score</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <TrendingUp className="w-5 h-5 text-emerald-400 mb-2" />
              <p className="text-2xl font-bold text-white">
                {overview.stream_score.growth_score.toFixed(0)}
              </p>
              <p className="text-[10px] text-zinc-500 uppercase">Growth Score</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <Target className="w-5 h-5 text-cyan-400 mb-2" />
              <p className="text-2xl font-bold text-white">
                {overview.stream_score.consistency_score.toFixed(0)}
              </p>
              <p className="text-[10px] text-zinc-500 uppercase">Consistency</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Weekly Summary */}
      {overview?.weekly_summary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {[
            { label: "Streams", value: overview.weekly_summary.total_streams, icon: Calendar },
            { label: "Avg Score", value: overview.weekly_summary.avg_score.toFixed(1), icon: Star },
            { label: "Peak Viewers", value: overview.weekly_summary.total_viewers.toLocaleString(), icon: Users },
            { label: "New Followers", value: overview.weekly_summary.total_followers.toLocaleString(), icon: TrendingUp },
            { label: "Chat Messages", value: overview.weekly_summary.total_messages.toLocaleString(), icon: MessageSquare },
          ].map((item) => (
            <Card key={item.label} className="bg-zinc-900/30 border-zinc-800/50">
              <CardContent className="p-3">
                <div className="flex items-center gap-2">
                  <item.icon className="w-4 h-4 text-zinc-500" />
                  <span className="text-xs text-zinc-500">{item.label}</span>
                </div>
                <p className="text-lg font-semibold text-white mt-1">{item.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Tabs defaultValue="history" className="space-y-4">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="history" className="data-[state=active]:bg-zinc-800">
            Stream History
          </TabsTrigger>
          <TabsTrigger value="best-times" className="data-[state=active]:bg-zinc-800">
            Best Times
          </TabsTrigger>
          <TabsTrigger value="games" className="data-[state=active]:bg-zinc-800">
            Game Insights
          </TabsTrigger>
          <TabsTrigger value="record" className="data-[state=active]:bg-zinc-800">
            Record Session
          </TabsTrigger>
        </TabsList>

        {/* Stream History */}
        <TabsContent value="history" className="space-y-4">
          {chartData.length > 0 ? (
            <>
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-emerald-400" />
                    Stream Score Trend
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="date" tick={{ fill: "#71717a", fontSize: 11 }} />
                      <YAxis domain={[0, 100]} tick={{ fill: "#71717a", fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
                        labelStyle={{ color: "#a1a1aa" }}
                      />
                      <Area type="monotone" dataKey="score" stroke="#10b981" fill="url(#scoreGrad)" strokeWidth={2} name="Score" />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <div className="space-y-2">
                {overview?.recent_sessions.map((s) => (
                  <Card key={s.id} className="bg-zinc-900/30 border-zinc-800/50">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`text-2xl font-bold ${formatScore(s.stream_score)}`}>
                            {s.stream_score > 0 ? s.stream_score.toFixed(0) : "LIVE"}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-white">{s.title}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                              <Badge variant="outline" className="text-[10px] border-zinc-700 text-zinc-400">
                                <Gamepad2 className="w-3 h-3 mr-1" />
                                {s.game}
                              </Badge>
                              <span className="text-[10px] text-zinc-600">
                                {new Date(s.started_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-zinc-400">
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {s.peak_viewers} peak
                          </span>
                          <span className="flex items-center gap-1">
                            <MessageSquare className="w-3 h-3" />
                            {s.chat_messages.toLocaleString()}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {s.duration_minutes > 0 ? `${Math.floor(s.duration_minutes / 60)}h ${s.duration_minutes % 60}m` : "Live"}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Activity className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No stream data yet</p>
                <p className="text-zinc-600 text-xs mt-1">
                  Go to the Record Session tab to log your first stream
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Best Times */}
        <TabsContent value="best-times" className="space-y-4">
          {bestTimesChart.length > 0 ? (
            <>
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-cyan-400" />
                    Best Times to Stream (by recommendation score)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={bestTimesChart}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="label" tick={{ fill: "#71717a", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
                        labelStyle={{ color: "#a1a1aa" }}
                      />
                      <Bar dataKey="score" fill="#06b6d4" radius={[4, 4, 0, 0]} name="Recommendation" />
                      <Bar dataKey="competition" fill="#ef4444" radius={[4, 4, 0, 0]} name="Competition" opacity={0.5} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {overview?.best_times.map((t, i) => (
                  <Card key={i} className="bg-zinc-900/30 border-zinc-800/50">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-lg font-bold text-white">
                          {DAYS[t.day_of_week]} {t.hour}:00
                        </span>
                        <Badge className={`${t.recommended_score >= 85 ? "bg-emerald-500/20 text-emerald-400" : "bg-blue-500/20 text-blue-400"} text-xs`}>
                          {t.recommended_score.toFixed(0)}%
                        </Badge>
                      </div>
                      <div className="space-y-1 text-xs text-zinc-400">
                        <p>Competition: {t.competition_score.toFixed(0)}% ({t.active_streamers} streamers)</p>
                        <p>Avg category viewers: {t.avg_category_viewers.toLocaleString()}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Clock className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No best time data available yet</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Game Insights */}
        <TabsContent value="games" className="space-y-4">
          {overview?.game_recommendations && overview.game_recommendations.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {overview.game_recommendations.map((g) => (
                <Card key={g.game} className="bg-zinc-900/30 border-zinc-800/50">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Gamepad2 className="w-5 h-5 text-violet-400" />
                        <span className="font-medium text-white">{g.game}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {g.trending && (
                          <Badge className="bg-amber-500/20 text-amber-400 text-[10px]">
                            Trending
                          </Badge>
                        )}
                        <Badge className={`text-[10px] ${
                          g.competition_level === "low" ? "bg-emerald-500/20 text-emerald-400" :
                          g.competition_level === "medium" ? "bg-blue-500/20 text-blue-400" :
                          "bg-red-500/20 text-red-400"
                        }`}>
                          {g.competition_level} competition
                        </Badge>
                      </div>
                    </div>
                    <div className="space-y-1 text-xs text-zinc-400">
                      <p>Growth potential: <span className={formatScore(g.growth_potential)}>{g.growth_potential.toFixed(0)}/100</span></p>
                      <p>Avg viewers: {g.avg_viewers_in_category.toLocaleString()}</p>
                      <p className="text-zinc-500">{g.reason}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Gamepad2 className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No game data yet. Record more streams to get recommendations.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Record Session */}
        <TabsContent value="record" className="space-y-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <PlusCircle className="w-4 h-4 text-emerald-400" />
                Record Stream Session
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div>
                  <Label className="text-xs text-zinc-500">Game</Label>
                  <Input
                    className="bg-zinc-800 border-zinc-700 mt-1"
                    value={sessionForm.game}
                    onChange={(e) => setSessionForm({ ...sessionForm, game: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">Title</Label>
                  <Input
                    className="bg-zinc-800 border-zinc-700 mt-1"
                    value={sessionForm.title}
                    onChange={(e) => setSessionForm({ ...sessionForm, title: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">Duration (min)</Label>
                  <Input
                    type="number"
                    className="bg-zinc-800 border-zinc-700 mt-1"
                    value={sessionForm.duration_minutes}
                    onChange={(e) => setSessionForm({ ...sessionForm, duration_minutes: +e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">Peak Viewers</Label>
                  <Input
                    type="number"
                    className="bg-zinc-800 border-zinc-700 mt-1"
                    value={sessionForm.peak_viewers}
                    onChange={(e) => setSessionForm({ ...sessionForm, peak_viewers: +e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">Avg Viewers</Label>
                  <Input
                    type="number"
                    className="bg-zinc-800 border-zinc-700 mt-1"
                    value={sessionForm.avg_viewers}
                    onChange={(e) => setSessionForm({ ...sessionForm, avg_viewers: +e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">Chat Messages</Label>
                  <Input
                    type="number"
                    className="bg-zinc-800 border-zinc-700 mt-1"
                    value={sessionForm.chat_messages}
                    onChange={(e) => setSessionForm({ ...sessionForm, chat_messages: +e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">New Followers</Label>
                  <Input
                    type="number"
                    className="bg-zinc-800 border-zinc-700 mt-1"
                    value={sessionForm.new_followers}
                    onChange={(e) => setSessionForm({ ...sessionForm, new_followers: +e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">New Subscribers</Label>
                  <Input
                    type="number"
                    className="bg-zinc-800 border-zinc-700 mt-1"
                    value={sessionForm.new_subscribers}
                    onChange={(e) => setSessionForm({ ...sessionForm, new_subscribers: +e.target.value })}
                  />
                </div>
              </div>
              <Button
                className="mt-4 bg-emerald-600 hover:bg-emerald-700"
                onClick={recordSession}
              >
                <PlusCircle className="w-4 h-4 mr-2" />
                Record Session
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
