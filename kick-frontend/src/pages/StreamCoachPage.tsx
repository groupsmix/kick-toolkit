import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import {
  Brain,
  Play,
  Square,
  MessageSquare,
  TrendingUp,
  Users,
  Clock,
  Zap,
  AlertTriangle,
  Info,
  X,
  Settings,
  Sparkles,
  Activity,
  Eye,
  Gamepad2,
  Coffee,
  RefreshCw,
} from "lucide-react";

interface CoachSettings {
  channel: string;
  enabled: boolean;
  engagement_alerts: boolean;
  game_duration_alerts: boolean;
  viewer_change_alerts: boolean;
  raid_welcome_alerts: boolean;
  sentiment_alerts: boolean;
  break_reminders: boolean;
  break_reminder_minutes: number;
  engagement_drop_threshold: number;
  viewer_change_threshold: number;
}

interface StreamSession {
  id: string;
  channel: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  peak_viewers: number;
  avg_viewers: number;
  total_messages: number;
  game: string;
}

interface CoachSuggestion {
  id: string;
  session_id: string;
  channel: string;
  type: string;
  priority: string;
  title: string;
  message: string;
  dismissed: boolean;
  created_at: string;
  dismissed_at: string | null;
}

interface AnalysisResult {
  suggestions: CoachSuggestion[];
  metrics: {
    viewer_count: number;
    peak_viewers: number;
    avg_viewers: number;
    total_messages: number;
    stream_duration_minutes: number;
    game: string;
    snapshot_count: number;
  };
}

interface ActiveSessionResponse {
  session: StreamSession | null;
  active: boolean;
}

const PRIORITY_CONFIG = {
  action: {
    icon: Zap,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    badge: "bg-emerald-500/20 text-emerald-400",
  },
  warning: {
    icon: AlertTriangle,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    badge: "bg-amber-500/20 text-amber-400",
  },
  info: {
    icon: Info,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    badge: "bg-blue-500/20 text-blue-400",
  },
};

const TYPE_ICONS: Record<string, typeof Brain> = {
  engagement: MessageSquare,
  game_duration: Gamepad2,
  raid: Users,
  viewer_change: TrendingUp,
  sentiment: Activity,
  break: Coffee,
  peak_moment: Zap,
};

export function StreamCoachPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [activeSession, setActiveSession] = useState<StreamSession | null>(null);
  const [suggestions, setSuggestions] = useState<CoachSuggestion[]>([]);
  const [settings, setSettings] = useState<CoachSettings | null>(null);
  const [metrics, setMetrics] = useState<AnalysisResult["metrics"] | null>(null);
  const [aiInsights, setAiInsights] = useState<string>("");
  const [pastSessions, setPastSessions] = useState<StreamSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [viewerCount, setViewerCount] = useState(0);
  const [gameName, setGameName] = useState("");
  const [showSettings, setShowSettings] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [settingsData, sessionData, sessionsData] = await Promise.all([
        api<CoachSettings>(`/api/coach/settings/${channel}`),
        api<ActiveSessionResponse>(`/api/coach/session/active/${channel}`),
        api<StreamSession[]>(`/api/coach/sessions/${channel}?limit=10`),
      ]);
      setSettings(settingsData);
      setPastSessions(sessionsData);

      if (sessionData.active && sessionData.session) {
        setActiveSession(sessionData.session);
        setGameName(sessionData.session.game || "");
        const suggestionsData = await api<CoachSuggestion[]>(
          `/api/coach/suggestions/${sessionData.session.id}`
        );
        setSuggestions(suggestionsData);
      } else {
        setActiveSession(null);
        setSuggestions([]);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load coach data";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [channel]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  // Auto-refresh suggestions every 30s when session is active
  useEffect(() => {
    if (!activeSession) return;
    const interval = setInterval(async () => {
      try {
        const suggestionsData = await api<CoachSuggestion[]>(
          `/api/coach/suggestions/${activeSession.id}`
        );
        setSuggestions(suggestionsData);
      } catch {
        // silently retry next interval
      }
    }, 30_000);
    return () => clearInterval(interval);
  }, [activeSession]);

  const startSession = async () => {
    try {
      const session = await api<StreamSession>("/api/coach/session/start", {
        method: "POST",
        body: JSON.stringify({ channel, game: gameName }),
      });
      setActiveSession(session);
      setSuggestions([]);
      setMetrics(null);
      toast.success("Coaching session started!");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to start session");
    }
  };

  const endSession = async () => {
    if (!activeSession) return;
    try {
      await api(`/api/coach/session/${activeSession.id}/end`, { method: "POST" });
      setActiveSession(null);
      setSuggestions([]);
      setMetrics(null);
      toast.success("Coaching session ended.");
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to end session");
    }
  };

  const runAnalysis = async () => {
    if (!activeSession) return;
    setAnalyzing(true);
    try {
      const result = await api<AnalysisResult>("/api/coach/analyze", {
        method: "POST",
        body: JSON.stringify({
          channel,
          session_id: activeSession.id,
          viewer_count: viewerCount,
          game: gameName,
        }),
      });
      setMetrics(result.metrics);
      if (result.suggestions.length > 0) {
        setSuggestions((prev) => [...result.suggestions, ...prev]);
        toast.success(`${result.suggestions.length} new suggestion(s)!`);
      } else {
        toast.info("No new suggestions — keep it up!");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  const dismissSuggestion = async (id: string) => {
    try {
      await api(`/api/coach/suggestions/${id}/dismiss`, { method: "POST" });
      setSuggestions((prev) => prev.filter((s) => s.id !== id));
    } catch {
      toast.error("Failed to dismiss");
    }
  };

  const dismissAll = async () => {
    if (!activeSession) return;
    try {
      await api(`/api/coach/suggestions/${activeSession.id}/dismiss-all`, { method: "POST" });
      setSuggestions([]);
      toast.success("All suggestions dismissed");
    } catch {
      toast.error("Failed to dismiss all");
    }
  };

  const fetchInsights = async () => {
    if (!activeSession) return;
    setInsightsLoading(true);
    try {
      const data = await api<{ insights: string }>(`/api/coach/insights/${activeSession.id}`);
      setAiInsights(data.insights);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load insights");
    } finally {
      setInsightsLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!settings) return;
    try {
      await api(`/api/coach/settings/${channel}`, {
        method: "PUT",
        body: JSON.stringify(settings),
      });
      toast.success("Settings saved!");
      setShowSettings(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save settings");
    }
  };

  const formatDuration = (minutes: number) => {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  const formatTime = (ts: string) => {
    return new Date(ts).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-violet-500/20 via-purple-500/10 to-transparent border border-violet-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Brain className="w-6 h-6 text-violet-400" />
              <h2 className="text-2xl font-bold text-white">AI Stream Coach</h2>
              <Badge className="bg-violet-500/20 text-violet-400 border-violet-500/30 text-[10px] uppercase font-bold">
                Premium
              </Badge>
            </div>
            <p className="text-zinc-400">
              Real-time coaching suggestions to improve your stream performance and viewer engagement.
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="text-zinc-400 hover:text-white"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="w-5 h-5" />
          </Button>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <Brain className="w-32 h-32 text-violet-500" />
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && settings && (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Coach Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="flex items-center justify-between">
                <Label className="text-zinc-300 text-sm">Coach Enabled</Label>
                <Switch
                  checked={settings.enabled}
                  onCheckedChange={(v) => setSettings({ ...settings, enabled: v })}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-zinc-300 text-sm">Engagement Alerts</Label>
                <Switch
                  checked={settings.engagement_alerts}
                  onCheckedChange={(v) => setSettings({ ...settings, engagement_alerts: v })}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-zinc-300 text-sm">Game Duration Alerts</Label>
                <Switch
                  checked={settings.game_duration_alerts}
                  onCheckedChange={(v) => setSettings({ ...settings, game_duration_alerts: v })}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-zinc-300 text-sm">Viewer Change Alerts</Label>
                <Switch
                  checked={settings.viewer_change_alerts}
                  onCheckedChange={(v) => setSettings({ ...settings, viewer_change_alerts: v })}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-zinc-300 text-sm">Raid Welcome Alerts</Label>
                <Switch
                  checked={settings.raid_welcome_alerts}
                  onCheckedChange={(v) => setSettings({ ...settings, raid_welcome_alerts: v })}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-zinc-300 text-sm">Sentiment Alerts</Label>
                <Switch
                  checked={settings.sentiment_alerts}
                  onCheckedChange={(v) => setSettings({ ...settings, sentiment_alerts: v })}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-zinc-300 text-sm">Break Reminders</Label>
                <Switch
                  checked={settings.break_reminders}
                  onCheckedChange={(v) => setSettings({ ...settings, break_reminders: v })}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-zinc-300 text-sm">Break Interval (min)</Label>
                <Input
                  type="number"
                  value={settings.break_reminder_minutes}
                  onChange={(e) =>
                    setSettings({ ...settings, break_reminder_minutes: parseInt(e.target.value) || 120 })
                  }
                  className="bg-zinc-800 border-zinc-700 text-white h-8"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-zinc-300 text-sm">Viewer Change Threshold</Label>
                <Input
                  type="number"
                  value={settings.viewer_change_threshold}
                  onChange={(e) =>
                    setSettings({ ...settings, viewer_change_threshold: parseInt(e.target.value) || 10 })
                  }
                  className="bg-zinc-800 border-zinc-700 text-white h-8"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="text-zinc-400"
                onClick={() => setShowSettings(false)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                className="bg-violet-500 hover:bg-violet-600 text-white"
                onClick={saveSettings}
              >
                Save Settings
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Session Control */}
      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardContent className="p-4">
          {!activeSession ? (
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <div className="flex-1 flex items-center gap-3 w-full sm:w-auto">
                <Input
                  placeholder="Game / Activity name..."
                  value={gameName}
                  onChange={(e) => setGameName(e.target.value)}
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <Button
                className="bg-emerald-500 hover:bg-emerald-600 text-black font-semibold w-full sm:w-auto"
                onClick={startSession}
              >
                <Play className="w-4 h-4 mr-2" />
                Start Coaching Session
              </Button>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-sm text-emerald-400 font-medium">Live Coaching</span>
                </div>
                <Separator orientation="vertical" className="h-4 bg-zinc-700 hidden sm:block" />
                <span className="text-xs text-zinc-500">
                  Started {formatTime(activeSession.started_at)}
                </span>
                {activeSession.game && (
                  <>
                    <Separator orientation="vertical" className="h-4 bg-zinc-700 hidden sm:block" />
                    <span className="text-xs text-zinc-400 flex items-center gap-1">
                      <Gamepad2 className="w-3 h-3" />
                      {activeSession.game}
                    </span>
                  </>
                )}
              </div>
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <div className="flex items-center gap-2 flex-1">
                  <Input
                    type="number"
                    placeholder="Viewers"
                    value={viewerCount || ""}
                    onChange={(e) => setViewerCount(parseInt(e.target.value) || 0)}
                    className="bg-zinc-800 border-zinc-700 text-white w-24 h-8 text-sm"
                  />
                  <Input
                    placeholder="Game"
                    value={gameName}
                    onChange={(e) => setGameName(e.target.value)}
                    className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                  />
                </div>
                <Button
                  size="sm"
                  className="bg-violet-500 hover:bg-violet-600 text-white"
                  onClick={runAnalysis}
                  disabled={analyzing}
                >
                  {analyzing ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Brain className="w-4 h-4" />
                  )}
                  <span className="ml-1 hidden sm:inline">Analyze</span>
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                  onClick={endSession}
                >
                  <Square className="w-3 h-3 mr-1" />
                  End
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {activeSession && (
        <Tabs defaultValue="suggestions" className="space-y-4">
          <TabsList className="bg-zinc-900 border border-zinc-800">
            <TabsTrigger value="suggestions" className="data-[state=active]:bg-zinc-800">
              Suggestions {suggestions.length > 0 && `(${suggestions.length})`}
            </TabsTrigger>
            <TabsTrigger value="metrics" className="data-[state=active]:bg-zinc-800">
              Metrics
            </TabsTrigger>
            <TabsTrigger value="insights" className="data-[state=active]:bg-zinc-800">
              AI Insights
            </TabsTrigger>
          </TabsList>

          {/* Suggestions Tab */}
          <TabsContent value="suggestions" className="space-y-4">
            {/* Metrics Cards */}
            {metrics && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-3 flex items-center gap-2">
                    <Eye className="w-5 h-5 text-blue-400" />
                    <div>
                      <p className="text-lg font-bold text-white">{metrics.viewer_count}</p>
                      <p className="text-[10px] text-zinc-500 uppercase">Viewers</p>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-3 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-emerald-400" />
                    <div>
                      <p className="text-lg font-bold text-white">{metrics.peak_viewers}</p>
                      <p className="text-[10px] text-zinc-500 uppercase">Peak</p>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-3 flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-purple-400" />
                    <div>
                      <p className="text-lg font-bold text-white">{metrics.total_messages}</p>
                      <p className="text-[10px] text-zinc-500 uppercase">Messages</p>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-3 flex items-center gap-2">
                    <Clock className="w-5 h-5 text-amber-400" />
                    <div>
                      <p className="text-lg font-bold text-white">
                        {formatDuration(metrics.stream_duration_minutes)}
                      </p>
                      <p className="text-[10px] text-zinc-500 uppercase">Duration</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Suggestion Cards */}
            {suggestions.length > 0 ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-zinc-400">
                    Active Suggestions
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-zinc-500 hover:text-zinc-300 text-xs"
                    onClick={dismissAll}
                  >
                    Dismiss All
                  </Button>
                </div>
                {suggestions.map((suggestion) => {
                  const config = PRIORITY_CONFIG[suggestion.priority as keyof typeof PRIORITY_CONFIG] || PRIORITY_CONFIG.info;
                  const TypeIcon = TYPE_ICONS[suggestion.type] || Brain;
                  const PriorityIcon = config.icon;
                  return (
                    <Card
                      key={suggestion.id}
                      className={`${config.bg} ${config.border} border transition-all hover:scale-[1.01]`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg ${config.bg}`}>
                            <TypeIcon className={`w-5 h-5 ${config.color}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="text-sm font-semibold text-white">{suggestion.title}</h4>
                              <Badge className={`${config.badge} text-[10px] uppercase`}>
                                <PriorityIcon className="w-3 h-3 mr-1" />
                                {suggestion.priority}
                              </Badge>
                            </div>
                            <p className="text-sm text-zinc-300">{suggestion.message}</p>
                            <p className="text-[10px] text-zinc-600 mt-2">
                              {formatTime(suggestion.created_at)}
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-zinc-600 hover:text-zinc-300 h-6 w-6"
                            onClick={() => dismissSuggestion(suggestion.id)}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            ) : (
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-8 text-center">
                  <Brain className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                  <p className="text-zinc-400 text-sm">No active suggestions</p>
                  <p className="text-zinc-600 text-xs mt-1">
                    Enter your current viewer count and click Analyze to get coaching tips
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Metrics Tab */}
          <TabsContent value="metrics" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-violet-400" />
                    Session Overview
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-400">Status</span>
                    <Badge className="bg-emerald-500/20 text-emerald-400">
                      {activeSession.status}
                    </Badge>
                  </div>
                  <Separator className="bg-zinc-800" />
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-400">Started</span>
                    <span className="text-sm text-white">
                      {new Date(activeSession.started_at).toLocaleString()}
                    </span>
                  </div>
                  <Separator className="bg-zinc-800" />
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-400">Game</span>
                    <span className="text-sm text-white">{activeSession.game || "Not set"}</span>
                  </div>
                  <Separator className="bg-zinc-800" />
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-400">Peak Viewers</span>
                    <span className="text-sm text-white font-bold">
                      {metrics?.peak_viewers ?? activeSession.peak_viewers}
                    </span>
                  </div>
                  <Separator className="bg-zinc-800" />
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-400">Avg Viewers</span>
                    <span className="text-sm text-white">
                      {metrics?.avg_viewers ?? activeSession.avg_viewers}
                    </span>
                  </div>
                  <Separator className="bg-zinc-800" />
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-400">Total Messages</span>
                    <span className="text-sm text-white">
                      {metrics?.total_messages ?? activeSession.total_messages}
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                    Quick Tips
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-zinc-800/30">
                    <MessageSquare className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-zinc-300">
                      Ask your chat a question every 15-20 minutes to keep engagement high
                    </p>
                  </div>
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-zinc-800/30">
                    <Users className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-zinc-300">
                      Greet new viewers by name when you see them chatting for the first time
                    </p>
                  </div>
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-zinc-800/30">
                    <Gamepad2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-zinc-300">
                      Switch games or activities every 60-90 minutes to prevent viewer fatigue
                    </p>
                  </div>
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-zinc-800/30">
                    <Coffee className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-zinc-300">
                      Take 5-minute breaks every 2 hours — viewers appreciate when you take care of yourself
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* AI Insights Tab */}
          <TabsContent value="insights" className="space-y-4">
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-violet-400" />
                  AI-Powered Insights
                </CardTitle>
              </CardHeader>
              <CardContent>
                {!aiInsights ? (
                  <div className="text-center py-6">
                    <Sparkles className="w-10 h-10 text-zinc-700 mx-auto mb-3" />
                    <p className="text-sm text-zinc-400 mb-4">
                      Get AI-generated coaching insights based on your current stream data
                    </p>
                    <Button
                      className="bg-violet-500 hover:bg-violet-600 text-white"
                      onClick={fetchInsights}
                      disabled={insightsLoading}
                    >
                      {insightsLoading ? (
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Sparkles className="w-4 h-4 mr-2" />
                      )}
                      Generate Insights
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="prose prose-invert prose-sm max-w-none">
                      {aiInsights.split("\n").map((line, i) => (
                        <p key={i} className="text-sm text-zinc-300">
                          {line}
                        </p>
                      ))}
                    </div>
                    <Separator className="bg-zinc-800" />
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-violet-400 hover:text-violet-300"
                      onClick={fetchInsights}
                      disabled={insightsLoading}
                    >
                      {insightsLoading ? (
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4 mr-2" />
                      )}
                      Refresh Insights
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Past Sessions */}
      {pastSessions.length > 0 && (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Recent Coaching Sessions
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="max-h-64">
              <div className="divide-y divide-zinc-800/50">
                {pastSessions
                  .filter((s) => s.id !== activeSession?.id)
                  .map((session) => (
                    <div key={session.id} className="px-4 py-3 flex items-center justify-between hover:bg-zinc-800/30">
                      <div className="flex items-center gap-3">
                        <Badge
                          className={
                            session.status === "active"
                              ? "bg-emerald-500/20 text-emerald-400"
                              : "bg-zinc-700/50 text-zinc-400"
                          }
                        >
                          {session.status}
                        </Badge>
                        <div>
                          <p className="text-sm text-white">
                            {session.game || "No game"} — {new Date(session.started_at).toLocaleDateString()}
                          </p>
                          <p className="text-xs text-zinc-500">
                            Peak: {session.peak_viewers} viewers | Avg: {session.avg_viewers} | Messages: {session.total_messages}
                          </p>
                        </div>
                      </div>
                      {session.ended_at && (
                        <span className="text-xs text-zinc-600">
                          {formatTime(session.started_at)} - {formatTime(session.ended_at)}
                        </span>
                      )}
                    </div>
                  ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
