import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import { PageSkeleton } from "@/components/LoadingSkeleton";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  BarChart3,
  Users,
  Eye,
  Target,
  Sparkles,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  Star,
  PlusCircle,
  Activity,
  DollarSign,
  Clock,
} from "lucide-react";

interface StreamerSnapshot {
  id: string;
  channel: string;
  avg_viewers: number;
  peak_viewers: number;
  follower_count: number;
  subscriber_count: number;
  hours_streamed: number;
  chat_messages: number;
  categories: string[];
  recorded_at: string;
}

interface GrowthPrediction {
  id: string;
  channel: string;
  metric: string;
  current_value: number;
  predicted_value: number;
  predicted_date: string;
  confidence: number;
  trend: string;
  created_at: string;
}

interface GrowthComparison {
  id: string;
  channel: string;
  compared_channel: string;
  similarity_score: number;
  growth_phase: string;
  insight: string;
  created_at: string;
}

interface StockEntry {
  channel: string;
  stock_score: number;
  trend: string;
  change_pct: number;
  rank: number;
  avg_viewers: number;
  follower_count: number;
}

interface AnalyticsOverview {
  channel: string;
  growth_score: number;
  sponsorship_readiness: number;
  consistency_score: number;
  engagement_rate: number;
  trend: string;
  predictions: GrowthPrediction[];
  comparisons: GrowthComparison[];
  recent_snapshots: StreamerSnapshot[];
  stock: StockEntry | null;
}

const TREND_CONFIG = {
  rising: { icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-500/10", label: "Rising" },
  stable: { icon: Minus, color: "text-blue-400", bg: "bg-blue-500/10", label: "Stable" },
  declining: { icon: TrendingDown, color: "text-red-400", bg: "bg-red-500/10", label: "Declining" },
};

const METRIC_LABELS: Record<string, string> = {
  followers: "Followers",
  avg_viewers: "Avg Viewers",
  subscribers: "Subscribers",
};

export function AnalyticsPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [, setStockLeaderboard] = useState<StockEntry[]>([]);
  const [narrative, setNarrative] = useState("");
  const [loading, setLoading] = useState(true);
  const [predictionsLoading, setPredictionsLoading] = useState(false);
  const [comparisonsLoading, setComparisonsLoading] = useState(false);
  const [narrativeLoading, setNarrativeLoading] = useState(false);
  const [snapshotForm, setSnapshotForm] = useState({
    avg_viewers: 0,
    peak_viewers: 0,
    follower_count: 0,
    subscriber_count: 0,
    hours_streamed: 0,
    chat_messages: 0,
  });

  const fetchData = useCallback(async () => {
    try {
      const [overviewData, leaderboard] = await Promise.all([
        api<AnalyticsOverview>(`/api/analytics/overview/${channel}`),
        api<StockEntry[]>("/api/analytics/stock/leaderboard?limit=10"),
      ]);
      setOverview(overviewData);
      setStockLeaderboard(leaderboard);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load analytics";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [channel]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  const recordSnapshot = async () => {
    try {
      await api("/api/analytics/snapshots", {
        method: "POST",
        body: JSON.stringify({ channel, ...snapshotForm }),
      });
      toast.success("Snapshot recorded!");
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to record snapshot");
    }
  };

  const runPredictions = async () => {
    setPredictionsLoading(true);
    try {
      await api(`/api/analytics/predictions/${channel}`, { method: "POST" });
      toast.success("Predictions generated!");
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Not enough data for predictions");
    } finally {
      setPredictionsLoading(false);
    }
  };

  const runComparisons = async () => {
    setComparisonsLoading(true);
    try {
      await api(`/api/analytics/comparisons/${channel}`, { method: "POST" });
      toast.success("Comparisons generated!");
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to generate comparisons");
    } finally {
      setComparisonsLoading(false);
    }
  };

  const fetchNarrative = async () => {
    setNarrativeLoading(true);
    try {
      const data = await api<{ narrative: string }>(`/api/analytics/narrative/${channel}`);
      setNarrative(data.narrative);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load narrative");
    } finally {
      setNarrativeLoading(false);
    }
  };


  const trendConfig = (trend: string) =>
    TREND_CONFIG[trend as keyof typeof TREND_CONFIG] || TREND_CONFIG.stable;

  const formatNumber = (n: number) => {
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
    return n.toFixed(0);
  };

  const formatDate = (ts: string) =>
    new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric" });

  if (loading) {
    return <PageSkeleton />;
  }

  const chartData = overview?.recent_snapshots
    ? [...overview.recent_snapshots].reverse().map((s) => ({
        date: formatDate(s.recorded_at),
        viewers: s.avg_viewers,
        followers: s.follower_count,
        subscribers: s.subscriber_count,
        messages: s.chat_messages,
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-indigo-500/20 via-purple-500/10 to-transparent border border-indigo-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <BarChart3 className="w-6 h-6 text-indigo-400" />
              <h2 className="text-2xl font-bold text-white">Predictive Analytics</h2>
              <Badge className="bg-indigo-500/20 text-indigo-400 border-indigo-500/30 text-[10px] uppercase font-bold">
                Premium
              </Badge>
            </div>
            <p className="text-zinc-400">
              Track growth patterns, predict your trajectory, and see how you compare to other streamers.
            </p>
          </div>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <BarChart3 className="w-32 h-32 text-indigo-500" />
        </div>
      </div>

      {/* Score Cards */}
      {overview && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
                <Badge className={`${trendConfig(overview.trend).bg} ${trendConfig(overview.trend).color} text-[10px]`}>
                  {trendConfig(overview.trend).label}
                </Badge>
              </div>
              <p className="text-2xl font-bold text-white">{overview.growth_score}</p>
              <p className="text-[10px] text-zinc-500 uppercase">Growth Score</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <DollarSign className="w-5 h-5 text-amber-400" />
              </div>
              <p className="text-2xl font-bold text-white">{overview.sponsorship_readiness}</p>
              <p className="text-[10px] text-zinc-500 uppercase">Sponsorship Ready</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <Clock className="w-5 h-5 text-blue-400" />
              </div>
              <p className="text-2xl font-bold text-white">{overview.consistency_score}</p>
              <p className="text-[10px] text-zinc-500 uppercase">Consistency</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <Activity className="w-5 h-5 text-purple-400" />
              </div>
              <p className="text-2xl font-bold text-white">{overview.engagement_rate}</p>
              <p className="text-[10px] text-zinc-500 uppercase">Engagement Rate</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="growth" className="space-y-4">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="growth" className="data-[state=active]:bg-zinc-800">
            Growth
          </TabsTrigger>
          <TabsTrigger value="predictions" className="data-[state=active]:bg-zinc-800">
            Predictions
          </TabsTrigger>
          <TabsTrigger value="comparisons" className="data-[state=active]:bg-zinc-800">
            Comparisons
          </TabsTrigger>
          <TabsTrigger value="record" className="data-[state=active]:bg-zinc-800">
            Record Data
          </TabsTrigger>
        </TabsList>

        {/* Growth Tab */}
        <TabsContent value="growth" className="space-y-4">
          {chartData.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                    <Eye className="w-4 h-4 text-blue-400" />
                    Average Viewers
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={200}>
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="viewerGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="date" tick={{ fill: "#71717a", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
                        labelStyle={{ color: "#a1a1aa" }}
                      />
                      <Area type="monotone" dataKey="viewers" stroke="#6366f1" fill="url(#viewerGrad)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                    <Users className="w-4 h-4 text-emerald-400" />
                    Followers
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={200}>
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="followerGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="date" tick={{ fill: "#71717a", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
                        labelStyle={{ color: "#a1a1aa" }}
                      />
                      <Area type="monotone" dataKey="followers" stroke="#10b981" fill="url(#followerGrad)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="bg-zinc-900/50 border-zinc-800 lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-violet-400" />
                      AI Growth Narrative
                    </CardTitle>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-violet-400 hover:text-violet-300"
                      onClick={fetchNarrative}
                      disabled={narrativeLoading}
                    >
                      {narrativeLoading ? (
                        <RefreshCw className="w-4 h-4 animate-spin mr-1" />
                      ) : (
                        <Sparkles className="w-4 h-4 mr-1" />
                      )}
                      {narrative ? "Refresh" : "Generate"}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {narrative ? (
                    <div className="prose prose-invert prose-sm max-w-none">
                      {narrative.split("\n").map((line, i) => (
                        <p key={i} className="text-sm text-zinc-300 mb-2">
                          {line}
                        </p>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <Sparkles className="w-8 h-8 text-zinc-700 mx-auto mb-2" />
                      <p className="text-sm text-zinc-500">
                        Click Generate to get an AI-powered analysis of your growth trajectory
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <BarChart3 className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No growth data yet</p>
                <p className="text-zinc-600 text-xs mt-1">
                  Go to the Record Data tab to add your first snapshot
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Predictions Tab */}
        <TabsContent value="predictions" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-zinc-400">Growth Predictions (30-Day Forecast)</h3>
            <Button
              size="sm"
              className="bg-indigo-500 hover:bg-indigo-600 text-white"
              onClick={runPredictions}
              disabled={predictionsLoading}
            >
              {predictionsLoading ? (
                <RefreshCw className="w-4 h-4 animate-spin mr-1" />
              ) : (
                <Target className="w-4 h-4 mr-1" />
              )}
              Generate Predictions
            </Button>
          </div>

          {overview && overview.predictions.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {overview.predictions.map((pred) => {
                const tc = trendConfig(pred.trend);
                const TrendIcon = tc.icon;
                const changePct =
                  pred.current_value > 0
                    ? (((pred.predicted_value - pred.current_value) / pred.current_value) * 100).toFixed(1)
                    : "0";
                const isPositive = pred.predicted_value >= pred.current_value;

                return (
                  <Card key={pred.id} className={`bg-zinc-900/50 border-zinc-800`}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-zinc-300">
                          {METRIC_LABELS[pred.metric] || pred.metric}
                        </span>
                        <Badge className={`${tc.bg} ${tc.color} text-[10px]`}>
                          <TrendIcon className="w-3 h-3 mr-1" />
                          {tc.label}
                        </Badge>
                      </div>
                      <div className="flex items-end gap-2 mb-2">
                        <span className="text-2xl font-bold text-white">
                          {formatNumber(pred.predicted_value)}
                        </span>
                        <span className={`text-sm flex items-center ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
                          {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                          {changePct}%
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs text-zinc-500">
                        <span>Current: {formatNumber(pred.current_value)}</span>
                        <span>Confidence: {(pred.confidence * 100).toFixed(0)}%</span>
                      </div>
                      <div className="mt-2 w-full bg-zinc-800 rounded-full h-1.5">
                        <div
                          className="bg-indigo-500 h-1.5 rounded-full transition-all"
                          style={{ width: `${Math.min(100, pred.confidence * 100)}%` }}
                        />
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Target className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No predictions yet</p>
                <p className="text-zinc-600 text-xs mt-1">
                  Record at least 2 snapshots, then generate predictions
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Comparisons Tab */}
        <TabsContent value="comparisons" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-zinc-400">Growth Comparisons</h3>
            <Button
              size="sm"
              className="bg-purple-500 hover:bg-purple-600 text-white"
              onClick={runComparisons}
              disabled={comparisonsLoading}
            >
              {comparisonsLoading ? (
                <RefreshCw className="w-4 h-4 animate-spin mr-1" />
              ) : (
                <Users className="w-4 h-4 mr-1" />
              )}
              Find Similar Streamers
            </Button>
          </div>

          {overview && overview.comparisons.length > 0 ? (
            <div className="space-y-3">
              {overview.comparisons.map((comp) => (
                <Card key={comp.id} className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-purple-500/10">
                        <Star className="w-5 h-5 text-purple-400" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-sm font-semibold text-white">{comp.compared_channel}</h4>
                          <Badge className="bg-purple-500/20 text-purple-400 text-[10px]">
                            {comp.similarity_score}% match
                          </Badge>
                          <Badge className="bg-zinc-700/50 text-zinc-400 text-[10px]">
                            {comp.growth_phase}
                          </Badge>
                        </div>
                        <p className="text-sm text-zinc-300">{comp.insight}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Users className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No comparisons yet</p>
                <p className="text-zinc-600 text-xs mt-1">
                  Click &quot;Find Similar Streamers&quot; to compare your growth curve
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Record Data Tab */}
        <TabsContent value="record" className="space-y-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <PlusCircle className="w-4 h-4 text-emerald-400" />
                Record Daily Snapshot
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-xs text-zinc-500">
                Record your daily stream metrics to build growth data for predictions and comparisons.
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <div className="space-y-1">
                  <Label className="text-zinc-400 text-xs">Avg Viewers</Label>
                  <Input
                    type="number"
                    value={snapshotForm.avg_viewers || ""}
                    onChange={(e) =>
                      setSnapshotForm({ ...snapshotForm, avg_viewers: parseFloat(e.target.value) || 0 })
                    }
                    className="bg-zinc-800 border-zinc-700 text-white h-9"
                    placeholder="0"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-zinc-400 text-xs">Peak Viewers</Label>
                  <Input
                    type="number"
                    value={snapshotForm.peak_viewers || ""}
                    onChange={(e) =>
                      setSnapshotForm({ ...snapshotForm, peak_viewers: parseInt(e.target.value) || 0 })
                    }
                    className="bg-zinc-800 border-zinc-700 text-white h-9"
                    placeholder="0"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-zinc-400 text-xs">Followers</Label>
                  <Input
                    type="number"
                    value={snapshotForm.follower_count || ""}
                    onChange={(e) =>
                      setSnapshotForm({ ...snapshotForm, follower_count: parseInt(e.target.value) || 0 })
                    }
                    className="bg-zinc-800 border-zinc-700 text-white h-9"
                    placeholder="0"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-zinc-400 text-xs">Subscribers</Label>
                  <Input
                    type="number"
                    value={snapshotForm.subscriber_count || ""}
                    onChange={(e) =>
                      setSnapshotForm({ ...snapshotForm, subscriber_count: parseInt(e.target.value) || 0 })
                    }
                    className="bg-zinc-800 border-zinc-700 text-white h-9"
                    placeholder="0"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-zinc-400 text-xs">Hours Streamed</Label>
                  <Input
                    type="number"
                    value={snapshotForm.hours_streamed || ""}
                    onChange={(e) =>
                      setSnapshotForm({ ...snapshotForm, hours_streamed: parseFloat(e.target.value) || 0 })
                    }
                    className="bg-zinc-800 border-zinc-700 text-white h-9"
                    placeholder="0"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-zinc-400 text-xs">Chat Messages</Label>
                  <Input
                    type="number"
                    value={snapshotForm.chat_messages || ""}
                    onChange={(e) =>
                      setSnapshotForm({ ...snapshotForm, chat_messages: parseInt(e.target.value) || 0 })
                    }
                    className="bg-zinc-800 border-zinc-700 text-white h-9"
                    placeholder="0"
                  />
                </div>
              </div>
              <Button
                className="bg-emerald-500 hover:bg-emerald-600 text-black font-semibold w-full"
                onClick={recordSnapshot}
              >
                <PlusCircle className="w-4 h-4 mr-2" />
                Record Snapshot
              </Button>
            </CardContent>
          </Card>

          {/* Recent Snapshots */}
          {overview && overview.recent_snapshots.length > 0 && (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm text-zinc-400">Recent Snapshots</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="max-h-64">
                  <div className="divide-y divide-zinc-800/50">
                    {overview.recent_snapshots.map((snap) => (
                      <div key={snap.id} className="px-4 py-3 flex items-center justify-between">
                        <div>
                          <p className="text-sm text-white">
                            {formatDate(snap.recorded_at)}
                          </p>
                          <p className="text-[10px] text-zinc-500">
                            {snap.hours_streamed}h streamed · {snap.chat_messages} messages
                          </p>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-zinc-400">
                          <span className="flex items-center gap-1">
                            <Eye className="w-3 h-3 text-blue-400" />
                            {snap.avg_viewers}
                          </span>
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3 text-emerald-400" />
                            {formatNumber(snap.follower_count)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
