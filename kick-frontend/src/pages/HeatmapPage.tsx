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
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Map,
  Users,
  Eye,
  Clock,
  AlertTriangle,
  Info,
  Zap,
  Activity,
  RefreshCw,
  Gamepad2,
  Target,
  BarChart3,
  Layers,
} from "lucide-react";

interface HeatmapOverview {
  channel: string;
  total_sessions: number;
  avg_session_duration: number;
  avg_retention_rate: number;
  peak_viewer_minute: number;
  best_category: string;
  worst_category: string;
  unique_viewers: number;
  insights: Insight[];
  timeline: TimelinePoint[];
  category_stats: CategoryStat[];
}

interface Insight {
  type: string;
  priority: string;
  title: string;
  message: string;
  metric: string;
}

interface TimelinePoint {
  minute_offset: number;
  avg_viewers: number;
  avg_messages: number;
  avg_chatters: number;
}

interface CategoryStat {
  category: string;
  segment_count: number;
  avg_viewers: number;
  avg_retention: number;
  total_chat: number;
}

const PRIORITY_STYLES: Record<string, { icon: typeof Info; color: string; bg: string }> = {
  action: { icon: Zap, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  warning: { icon: AlertTriangle, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
  info: { icon: Info, color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
};

export function HeatmapPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [overview, setOverview] = useState<HeatmapOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [segmentForm, setSegmentForm] = useState({
    session_id: "",
    label: "",
    category: "gaming",
    started_at: "",
    ended_at: "",
    viewer_count_start: 0,
    viewer_count_end: 0,
  });
  const [snapshotForm, setSnapshotForm] = useState({
    session_id: "",
    minute_offset: 0,
    viewer_count: 0,
    message_count: 0,
    unique_chatters: 0,
    category: "",
  });

  const fetchData = useCallback(async () => {
    try {
      const data = await api<HeatmapOverview>(`/api/heatmap/overview/${channel}`);
      setOverview(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load heatmap data";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [channel]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  const recordSnapshot = async () => {
    if (!snapshotForm.session_id) {
      toast.error("Session ID is required");
      return;
    }
    try {
      await api("/api/heatmap/snapshot", {
        method: "POST",
        body: JSON.stringify({
          channel,
          stream_session_id: snapshotForm.session_id,
          minute_offset: snapshotForm.minute_offset,
          viewer_count: snapshotForm.viewer_count,
          message_count: snapshotForm.message_count,
          unique_chatters: snapshotForm.unique_chatters,
          category: snapshotForm.category,
        }),
      });
      toast.success("Heatmap snapshot recorded!");
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to record snapshot");
    }
  };

  const addSegment = async () => {
    if (!segmentForm.session_id || !segmentForm.label) {
      toast.error("Session ID and label are required");
      return;
    }
    try {
      await api(`/api/heatmap/segments/${segmentForm.session_id}?channel=${channel}`, {
        method: "POST",
        body: JSON.stringify({
          label: segmentForm.label,
          category: segmentForm.category,
          started_at: segmentForm.started_at || new Date().toISOString(),
          ended_at: segmentForm.ended_at || null,
          viewer_count_start: segmentForm.viewer_count_start,
          viewer_count_end: segmentForm.viewer_count_end,
        }),
      });
      toast.success("Content segment added!");
      setSegmentForm({ session_id: "", label: "", category: "gaming", started_at: "", ended_at: "", viewer_count_start: 0, viewer_count_end: 0 });
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to add segment");
    }
  };

  const timelineData = overview?.timeline?.map((t) => ({
    minute: t.minute_offset,
    viewers: Math.round(t.avg_viewers),
    messages: Math.round(t.avg_messages),
    chatters: Math.round(t.avg_chatters),
  })) || [];

  const categoryData = overview?.category_stats?.map((c) => ({
    category: c.category,
    viewers: Math.round(c.avg_viewers),
    retention: Math.round(c.avg_retention),
    segments: c.segment_count,
  })) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-orange-500/20 via-amber-500/10 to-transparent border border-orange-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Map className="w-6 h-6 text-orange-400" />
              <h2 className="text-2xl font-bold text-white">Viewer Heatmap</h2>
              <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/30 text-[10px] uppercase font-bold">
                Premium
              </Badge>
            </div>
            <p className="text-zinc-400">
              Track viewer behavior, visualize attention patterns, and discover what content keeps your audience engaged.
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-orange-400 hover:text-orange-300"
            onClick={fetchData}
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </Button>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <Map className="w-32 h-32 text-orange-500" />
        </div>
      </div>

      {/* Stats Cards */}
      {overview && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <Users className="w-5 h-5 text-orange-400" />
              </div>
              <p className="text-2xl font-bold text-white">{overview.unique_viewers}</p>
              <p className="text-[10px] text-zinc-500 uppercase">Unique Viewers</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <Clock className="w-5 h-5 text-blue-400" />
              </div>
              <p className="text-2xl font-bold text-white">{overview.avg_session_duration}m</p>
              <p className="text-[10px] text-zinc-500 uppercase">Avg Session</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <Target className="w-5 h-5 text-emerald-400" />
              </div>
              <p className="text-2xl font-bold text-white">{overview.avg_retention_rate}%</p>
              <p className="text-[10px] text-zinc-500 uppercase">Avg Retention</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <Zap className="w-5 h-5 text-amber-400" />
              </div>
              <p className="text-2xl font-bold text-white">{overview.peak_viewer_minute}m</p>
              <p className="text-[10px] text-zinc-500 uppercase">Peak Minute</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="heatmap" className="space-y-4">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="heatmap" className="data-[state=active]:bg-zinc-800">
            <Map className="w-4 h-4 mr-1" />
            Heatmap
          </TabsTrigger>
          <TabsTrigger value="categories" className="data-[state=active]:bg-zinc-800">
            <Layers className="w-4 h-4 mr-1" />
            Categories
          </TabsTrigger>
          <TabsTrigger value="insights" className="data-[state=active]:bg-zinc-800">
            <Activity className="w-4 h-4 mr-1" />
            Insights
          </TabsTrigger>
          <TabsTrigger value="record" className="data-[state=active]:bg-zinc-800">
            <BarChart3 className="w-4 h-4 mr-1" />
            Record Data
          </TabsTrigger>
        </TabsList>

        {/* Heatmap Tab */}
        <TabsContent value="heatmap" className="space-y-4">
          {timelineData.length > 0 ? (
            <div className="space-y-4">
              {/* Viewer Density Timeline */}
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                    <Eye className="w-4 h-4 text-orange-400" />
                    Viewer Density Over Stream Duration
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={timelineData}>
                      <defs>
                        <linearGradient id="heatGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis
                        dataKey="minute"
                        tick={{ fill: "#71717a", fontSize: 11 }}
                        label={{ value: "Minutes", position: "insideBottomRight", offset: -5, fill: "#71717a", fontSize: 11 }}
                      />
                      <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
                        labelStyle={{ color: "#a1a1aa" }}
                        labelFormatter={(v) => `Minute ${v}`}
                      />
                      <Area type="monotone" dataKey="viewers" stroke="#f97316" fill="url(#heatGrad)" strokeWidth={2} name="Avg Viewers" />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Chat Activity Timeline */}
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-blue-400" />
                    Chat Activity & Unique Chatters
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={200}>
                    <AreaChart data={timelineData}>
                      <defs>
                        <linearGradient id="msgGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="chatterGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="minute" tick={{ fill: "#71717a", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
                        labelStyle={{ color: "#a1a1aa" }}
                        labelFormatter={(v) => `Minute ${v}`}
                      />
                      <Area type="monotone" dataKey="messages" stroke="#6366f1" fill="url(#msgGrad)" strokeWidth={2} name="Messages" />
                      <Area type="monotone" dataKey="chatters" stroke="#10b981" fill="url(#chatterGrad)" strokeWidth={2} name="Chatters" />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Map className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No heatmap data yet</p>
                <p className="text-zinc-600 text-xs mt-1">
                  Go to the Record Data tab to start capturing viewer behavior during your streams
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Categories Tab */}
        <TabsContent value="categories" className="space-y-4">
          {categoryData.length > 0 ? (
            <div className="space-y-4">
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                    <Gamepad2 className="w-4 h-4 text-orange-400" />
                    Viewer Retention by Category
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={categoryData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="category" tick={{ fill: "#71717a", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
                        labelStyle={{ color: "#a1a1aa" }}
                      />
                      <Bar dataKey="retention" fill="#f97316" radius={[4, 4, 0, 0]} name="Retention %" />
                      <Bar dataKey="viewers" fill="#6366f1" radius={[4, 4, 0, 0]} name="Avg Viewers" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Category cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {overview?.category_stats?.map((cat, i) => {
                  const isTop = i === 0 && overview.category_stats.length > 1;
                  const isWorst = i === overview.category_stats.length - 1 && overview.category_stats.length > 1;
                  return (
                    <Card key={cat.category} className={`bg-zinc-900/50 ${isTop ? "border-emerald-500/30" : isWorst ? "border-red-500/30" : "border-zinc-800"}`}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-white capitalize">{cat.category}</span>
                          {isTop && (
                            <Badge className="bg-emerald-500/20 text-emerald-400 text-[10px]">Best</Badge>
                          )}
                          {isWorst && (
                            <Badge className="bg-red-500/20 text-red-400 text-[10px]">Needs Work</Badge>
                          )}
                        </div>
                        <div className="grid grid-cols-3 gap-2 mt-3">
                          <div>
                            <p className="text-lg font-bold text-white">{Math.round(cat.avg_retention)}%</p>
                            <p className="text-[10px] text-zinc-500">Retention</p>
                          </div>
                          <div>
                            <p className="text-lg font-bold text-white">{Math.round(cat.avg_viewers)}</p>
                            <p className="text-[10px] text-zinc-500">Avg Views</p>
                          </div>
                          <div>
                            <p className="text-lg font-bold text-white">{cat.segment_count}</p>
                            <p className="text-[10px] text-zinc-500">Segments</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Layers className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No category data yet</p>
                <p className="text-zinc-600 text-xs mt-1">
                  Add content segments to see how different content types affect viewer retention
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights" className="space-y-4">
          {overview?.insights && overview.insights.length > 0 ? (
            <div className="space-y-3">
              {overview.insights.map((insight, i) => {
                const style = PRIORITY_STYLES[insight.priority] || PRIORITY_STYLES.info;
                const Icon = style.icon;
                return (
                  <Card key={i} className={`bg-zinc-900/50 ${style.bg}`}>
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className={`mt-0.5 ${style.color}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="text-sm font-medium text-white">{insight.title}</h4>
                            {insight.metric && (
                              <Badge className={`${style.bg} ${style.color} text-xs font-bold`}>
                                {insight.metric}
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-zinc-400">{insight.message}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Activity className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No insights yet</p>
                <p className="text-zinc-600 text-xs mt-1">
                  Record more heatmap data to unlock actionable insights about your viewer behavior
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Record Data Tab */}
        <TabsContent value="record" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Record Snapshot */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-orange-400" />
                  Record Heatmap Snapshot
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <Label className="text-zinc-300 text-xs">Stream Session ID</Label>
                  <Input
                    placeholder="Session ID from AI Coach..."
                    value={snapshotForm.session_id}
                    onChange={(e) => setSnapshotForm({ ...snapshotForm, session_id: e.target.value })}
                    className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-zinc-300 text-xs">Minute Offset</Label>
                    <Input
                      type="number"
                      value={snapshotForm.minute_offset}
                      onChange={(e) => setSnapshotForm({ ...snapshotForm, minute_offset: parseInt(e.target.value) || 0 })}
                      className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-zinc-300 text-xs">Viewer Count</Label>
                    <Input
                      type="number"
                      value={snapshotForm.viewer_count}
                      onChange={(e) => setSnapshotForm({ ...snapshotForm, viewer_count: parseInt(e.target.value) || 0 })}
                      className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-zinc-300 text-xs">Message Count</Label>
                    <Input
                      type="number"
                      value={snapshotForm.message_count}
                      onChange={(e) => setSnapshotForm({ ...snapshotForm, message_count: parseInt(e.target.value) || 0 })}
                      className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-zinc-300 text-xs">Unique Chatters</Label>
                    <Input
                      type="number"
                      value={snapshotForm.unique_chatters}
                      onChange={(e) => setSnapshotForm({ ...snapshotForm, unique_chatters: parseInt(e.target.value) || 0 })}
                      className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                    />
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-zinc-300 text-xs">Category</Label>
                  <Input
                    placeholder="e.g., gaming, just chatting..."
                    value={snapshotForm.category}
                    onChange={(e) => setSnapshotForm({ ...snapshotForm, category: e.target.value })}
                    className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                  />
                </div>
                <Button
                  className="w-full bg-orange-500 hover:bg-orange-600 text-white"
                  onClick={recordSnapshot}
                  size="sm"
                >
                  Record Snapshot
                </Button>
              </CardContent>
            </Card>

            {/* Add Content Segment */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-blue-400" />
                  Add Content Segment
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <Label className="text-zinc-300 text-xs">Stream Session ID</Label>
                  <Input
                    placeholder="Session ID..."
                    value={segmentForm.session_id}
                    onChange={(e) => setSegmentForm({ ...segmentForm, session_id: e.target.value })}
                    className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-zinc-300 text-xs">Label</Label>
                    <Input
                      placeholder="e.g., Ranked Matches"
                      value={segmentForm.label}
                      onChange={(e) => setSegmentForm({ ...segmentForm, label: e.target.value })}
                      className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-zinc-300 text-xs">Category</Label>
                    <Input
                      placeholder="e.g., gaming"
                      value={segmentForm.category}
                      onChange={(e) => setSegmentForm({ ...segmentForm, category: e.target.value })}
                      className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-zinc-300 text-xs">Viewers Start</Label>
                    <Input
                      type="number"
                      value={segmentForm.viewer_count_start}
                      onChange={(e) => setSegmentForm({ ...segmentForm, viewer_count_start: parseInt(e.target.value) || 0 })}
                      className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-zinc-300 text-xs">Viewers End</Label>
                    <Input
                      type="number"
                      value={segmentForm.viewer_count_end}
                      onChange={(e) => setSegmentForm({ ...segmentForm, viewer_count_end: parseInt(e.target.value) || 0 })}
                      className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                    />
                  </div>
                </div>
                <Button
                  className="w-full bg-blue-500 hover:bg-blue-600 text-white"
                  onClick={addSegment}
                  size="sm"
                >
                  Add Segment
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
