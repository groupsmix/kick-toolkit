import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Scissors,
  Zap,
  TrendingUp,
  Clock,
  MessageSquare,
  Video,
  Upload,
  Sparkles,
  RefreshCw,
  Trash2,
  Send,
  ExternalLink,
  Film,
  Eye,
  AlertTriangle,
} from "lucide-react";

// Platform icons as text since we don't have brand icons
const PLATFORM_CONFIG: Record<
  string,
  { label: string; color: string; bg: string }
> = {
  tiktok: {
    label: "TikTok",
    color: "text-pink-400",
    bg: "bg-pink-500/10 border-pink-500/20",
  },
  youtube: {
    label: "YouTube Shorts",
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/20",
  },
  instagram: {
    label: "Instagram Reels",
    color: "text-purple-400",
    bg: "bg-purple-500/10 border-purple-500/20",
  },
};

interface HypeMoment {
  id: string;
  channel: string;
  session_id: string | null;
  timestamp_start: string;
  timestamp_end: string;
  intensity: number;
  trigger_type: string;
  message_count: number;
  peak_rate: number;
  sample_messages: string[];
  status: string;
  created_at: string;
}

interface GeneratedClip {
  id: string;
  channel: string;
  hype_moment_id: string | null;
  title: string;
  description: string;
  caption: string;
  file_path: string | null;
  thumbnail_path: string | null;
  duration_seconds: number;
  status: string;
  platform_specs: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

interface ClipPost {
  id: string;
  clip_id: string;
  platform: string;
  platform_post_id: string | null;
  post_url: string | null;
  status: string;
  caption: string;
  error_message: string | null;
  posted_at: string | null;
  created_at: string;
}

const INTENSITY_COLORS: Record<string, string> = {
  extreme: "text-red-400 bg-red-500/10 border-red-500/20",
  high: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  medium: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  low: "text-zinc-400 bg-zinc-500/10 border-zinc-500/20",
};

function intensityLabel(value: number): string {
  if (value >= 5) return "extreme";
  if (value >= 3) return "high";
  if (value >= 2) return "medium";
  return "low";
}

export function ClipsPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [hypeMoments, setHypeMoments] = useState<HypeMoment[]>([]);
  const [clips, setClips] = useState<GeneratedClip[]>([]);
  const [selectedClip, setSelectedClip] = useState<GeneratedClip | null>(null);
  const [clipPosts, setClipPosts] = useState<ClipPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [captionLoading, setCaptionLoading] = useState(false);
  const [captionStyle, setCaptionStyle] = useState("engaging");
  const [clipForm, setClipForm] = useState({
    title: "",
    description: "",
    duration_seconds: 30,
  });

  const fetchData = useCallback(async () => {
    try {
      const [momentsData, clipsData] = await Promise.all([
        api<HypeMoment[]>(`/api/clips/hype-moments/${channel}?limit=20`),
        api<GeneratedClip[]>(`/api/clips/list/${channel}?limit=20`),
      ]);
      setHypeMoments(momentsData);
      setClips(clipsData);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Failed to load clips data";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [channel]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  useEffect(() => {
    if (selectedClip) {
      api<ClipPost[]>(`/api/clips/${selectedClip.id}/posts`)
        .then(setClipPosts)
        .catch(() => setClipPosts([]));
    }
  }, [selectedClip]);

  const detectHypeMoments = async () => {
    setDetecting(true);
    try {
      const moments = await api<HypeMoment[]>(
        `/api/clips/hype-moments/detect/${channel}?window_minutes=60`,
        { method: "POST" }
      );
      if (moments.length > 0) {
        setHypeMoments((prev) => [...moments, ...prev]);
        toast.success(`Detected ${moments.length} hype moment(s)!`);
      } else {
        toast.info(
          "No hype moments detected in the last 60 minutes. Keep streaming!"
        );
      }
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to detect hype moments"
      );
    } finally {
      setDetecting(false);
    }
  };

  const createClip = async (hypeMomentId?: string) => {
    try {
      const clip = await api<GeneratedClip>("/api/clips/generate", {
        method: "POST",
        body: JSON.stringify({
          channel,
          hype_moment_id: hypeMomentId || null,
          title: clipForm.title || "Stream Highlight",
          description: clipForm.description,
          duration_seconds: clipForm.duration_seconds,
        }),
      });
      setClips((prev) => [clip, ...prev]);
      setSelectedClip(clip);
      setClipForm({ title: "", description: "", duration_seconds: 30 });
      toast.success("Clip created!");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to create clip"
      );
    }
  };

  const generateCaption = async () => {
    if (!selectedClip) return;
    setCaptionLoading(true);
    try {
      const data = await api<{ caption: string }>(
        `/api/clips/${selectedClip.id}/caption`,
        {
          method: "POST",
          body: JSON.stringify({ style: captionStyle }),
        }
      );
      setSelectedClip({ ...selectedClip, caption: data.caption });
      setClips((prev) =>
        prev.map((c) =>
          c.id === selectedClip.id ? { ...c, caption: data.caption } : c
        )
      );
      toast.success("Caption generated!");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to generate caption"
      );
    } finally {
      setCaptionLoading(false);
    }
  };

  const postToSocial = async (platform: string) => {
    if (!selectedClip) return;
    try {
      const post = await api<ClipPost>(
        `/api/clips/${selectedClip.id}/post`,
        {
          method: "POST",
          body: JSON.stringify({
            platform,
            caption: selectedClip.caption || "",
          }),
        }
      );
      setClipPosts((prev) => [post, ...prev]);
      toast.success(
        `Clip queued for ${PLATFORM_CONFIG[platform]?.label || platform}!`
      );
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to post clip");
    }
  };

  const deleteClip = async (clipId: string) => {
    try {
      await api(`/api/clips/${clipId}`, { method: "DELETE" });
      setClips((prev) => prev.filter((c) => c.id !== clipId));
      if (selectedClip?.id === clipId) {
        setSelectedClip(null);
        setClipPosts([]);
      }
      toast.success("Clip deleted");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to delete clip"
      );
    }
  };

  const formatTime = (ts: string) =>
    new Date(ts).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });

  const formatDate = (ts: string) =>
    new Date(ts).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  const chartData = hypeMoments
    .slice(0, 15)
    .reverse()
    .map((m) => ({
      time: formatTime(m.timestamp_start),
      intensity: m.intensity,
      messages: m.message_count,
    }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-pink-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-pink-500/20 via-rose-500/10 to-transparent border border-pink-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Scissors className="w-6 h-6 text-pink-400" />
              <h2 className="text-2xl font-bold text-white">
                AI Clip Pipeline
              </h2>
              <Badge className="bg-pink-500/20 text-pink-400 border-pink-500/30 text-[10px] uppercase font-bold">
                Premium
              </Badge>
            </div>
            <p className="text-zinc-400">
              Auto-detect hype moments, generate clips with AI captions, and
              post to TikTok, YouTube Shorts & Reels.
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-pink-400 hover:text-pink-300"
            onClick={detectHypeMoments}
            disabled={detecting}
          >
            {detecting ? (
              <RefreshCw className="w-4 h-4 animate-spin mr-1" />
            ) : (
              <Zap className="w-4 h-4 mr-1" />
            )}
            Detect Hype
          </Button>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <Scissors className="w-32 h-32 text-pink-500" />
        </div>
      </div>

      <Tabs defaultValue="moments" className="space-y-4">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger
            value="moments"
            className="data-[state=active]:bg-zinc-800"
          >
            <Zap className="w-4 h-4 mr-1" />
            Hype Moments
          </TabsTrigger>
          <TabsTrigger
            value="clips"
            className="data-[state=active]:bg-zinc-800"
          >
            <Film className="w-4 h-4 mr-1" />
            Clips
          </TabsTrigger>
          <TabsTrigger
            value="create"
            className="data-[state=active]:bg-zinc-800"
          >
            <Upload className="w-4 h-4 mr-1" />
            Create Clip
          </TabsTrigger>
        </TabsList>

        {/* Hype Moments Tab */}
        <TabsContent value="moments" className="space-y-4">
          {/* Intensity Chart */}
          {chartData.length > 0 && (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-pink-400" />
                  Hype Intensity Timeline
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={chartData}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#27272a"
                    />
                    <XAxis
                      dataKey="time"
                      tick={{ fill: "#71717a", fontSize: 11 }}
                    />
                    <YAxis
                      tick={{ fill: "#71717a", fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#18181b",
                        border: "1px solid #27272a",
                        borderRadius: 8,
                      }}
                      labelStyle={{ color: "#a1a1aa" }}
                    />
                    <Bar
                      dataKey="intensity"
                      fill="#ec4899"
                      radius={[4, 4, 0, 0]}
                      name="Intensity"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Moments List */}
          {hypeMoments.length > 0 ? (
            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {hypeMoments.map((moment) => {
                  const level = intensityLabel(moment.intensity);
                  const colorClass =
                    INTENSITY_COLORS[level] || INTENSITY_COLORS.low;
                  return (
                    <Card
                      key={moment.id}
                      className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors"
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Zap className="w-4 h-4 text-pink-400" />
                              <span className="text-sm font-medium text-white">
                                Chat Hype Spike
                              </span>
                              <Badge
                                className={`${colorClass} text-[10px] uppercase font-bold`}
                              >
                                {level} ({moment.intensity.toFixed(1)}x)
                              </Badge>
                              <Badge
                                variant="outline"
                                className="text-zinc-500 border-zinc-700 text-[10px]"
                              >
                                {moment.status}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-4 text-xs text-zinc-500 mb-2">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {formatTime(moment.timestamp_start)}
                              </span>
                              <span className="flex items-center gap-1">
                                <MessageSquare className="w-3 h-3" />
                                {moment.message_count} messages
                              </span>
                              <span className="flex items-center gap-1">
                                <TrendingUp className="w-3 h-3" />
                                {moment.peak_rate}/min
                              </span>
                            </div>
                            {moment.sample_messages.length > 0 && (
                              <div className="space-y-1 mt-2">
                                {moment.sample_messages
                                  .slice(0, 3)
                                  .map((msg, i) => (
                                    <p
                                      key={i}
                                      className="text-xs text-zinc-500 truncate max-w-md"
                                    >
                                      &ldquo;{msg}&rdquo;
                                    </p>
                                  ))}
                              </div>
                            )}
                          </div>
                          <Button
                            size="sm"
                            className="bg-pink-500/20 text-pink-400 hover:bg-pink-500/30 border-pink-500/20"
                            onClick={() => {
                              setClipForm({
                                title: `Hype Moment - ${formatTime(moment.timestamp_start)}`,
                                description: `Chat spike with ${moment.message_count} messages (${moment.intensity.toFixed(1)}x intensity)`,
                                duration_seconds: 30,
                              });
                              createClip(moment.id);
                            }}
                            disabled={moment.status === "clipped"}
                          >
                            <Scissors className="w-3 h-3 mr-1" />
                            {moment.status === "clipped"
                              ? "Clipped"
                              : "Clip It"}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </ScrollArea>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Zap className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">
                  No hype moments detected yet
                </p>
                <p className="text-zinc-600 text-xs mt-1">
                  Click &ldquo;Detect Hype&rdquo; to scan your recent chat
                  activity for spike moments
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Clips Tab */}
        <TabsContent value="clips" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Clips List */}
            <div className="lg:col-span-1">
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                    <Film className="w-4 h-4 text-pink-400" />
                    Your Clips ({clips.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  {clips.length > 0 ? (
                    <ScrollArea className="h-[450px]">
                      <div className="space-y-1 p-2">
                        {clips.map((clip) => (
                          <button
                            key={clip.id}
                            className={`w-full text-left p-3 rounded-lg transition-colors ${
                              selectedClip?.id === clip.id
                                ? "bg-pink-500/10 border border-pink-500/20"
                                : "hover:bg-zinc-800/50"
                            }`}
                            onClick={() => setSelectedClip(clip)}
                          >
                            <p className="text-sm font-medium text-white truncate">
                              {clip.title || "Untitled Clip"}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge
                                variant="outline"
                                className="text-[10px] text-zinc-500 border-zinc-700"
                              >
                                {clip.status}
                              </Badge>
                              <span className="text-[10px] text-zinc-600">
                                {clip.duration_seconds}s
                              </span>
                              <span className="text-[10px] text-zinc-600">
                                {formatDate(clip.created_at)}
                              </span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </ScrollArea>
                  ) : (
                    <div className="p-6 text-center">
                      <Video className="w-8 h-8 text-zinc-700 mx-auto mb-2" />
                      <p className="text-xs text-zinc-500">
                        No clips yet. Detect hype moments or create one
                        manually.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Clip Detail / Editor */}
            <div className="lg:col-span-2">
              {selectedClip ? (
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm text-white flex items-center gap-2">
                        <Video className="w-4 h-4 text-pink-400" />
                        {selectedClip.title || "Untitled Clip"}
                      </CardTitle>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-red-400 hover:text-red-300 h-8 w-8"
                        onClick={() => deleteClip(selectedClip.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Clip Preview Placeholder */}
                    <div className="aspect-[9/16] max-h-[300px] bg-zinc-800 rounded-lg flex items-center justify-center border border-zinc-700">
                      <div className="text-center">
                        <Film className="w-12 h-12 text-zinc-600 mx-auto mb-2" />
                        <p className="text-xs text-zinc-500">
                          Clip Preview
                        </p>
                        <p className="text-[10px] text-zinc-600 mt-1">
                          Upload a clip or link a VOD timestamp
                        </p>
                      </div>
                    </div>

                    {/* Description */}
                    {selectedClip.description && (
                      <p className="text-xs text-zinc-400">
                        {selectedClip.description}
                      </p>
                    )}

                    <Separator className="bg-zinc-800" />

                    {/* AI Caption */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-zinc-300 text-sm flex items-center gap-1">
                          <Sparkles className="w-3 h-3 text-violet-400" />
                          AI Caption
                        </Label>
                        <div className="flex items-center gap-2">
                          <Select
                            value={captionStyle}
                            onValueChange={setCaptionStyle}
                          >
                            <SelectTrigger className="w-[120px] h-7 bg-zinc-800 border-zinc-700 text-xs text-white">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-zinc-900 border-zinc-700">
                              <SelectItem value="engaging">
                                Engaging
                              </SelectItem>
                              <SelectItem value="funny">
                                Funny
                              </SelectItem>
                              <SelectItem value="informative">
                                Informative
                              </SelectItem>
                              <SelectItem value="trending">
                                Trending
                              </SelectItem>
                            </SelectContent>
                          </Select>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-violet-400 hover:text-violet-300 h-7"
                            onClick={generateCaption}
                            disabled={captionLoading}
                          >
                            {captionLoading ? (
                              <RefreshCw className="w-3 h-3 animate-spin mr-1" />
                            ) : (
                              <Sparkles className="w-3 h-3 mr-1" />
                            )}
                            Generate
                          </Button>
                        </div>
                      </div>
                      {selectedClip.caption ? (
                        <div className="p-3 bg-zinc-800/50 rounded-lg border border-zinc-700">
                          <p className="text-sm text-zinc-300">
                            {selectedClip.caption}
                          </p>
                        </div>
                      ) : (
                        <p className="text-xs text-zinc-600 italic">
                          No caption yet. Click Generate to create one with
                          AI.
                        </p>
                      )}
                    </div>

                    <Separator className="bg-zinc-800" />

                    {/* Post to Social */}
                    <div className="space-y-3">
                      <Label className="text-zinc-300 text-sm flex items-center gap-1">
                        <Send className="w-3 h-3 text-pink-400" />
                        Post to Social Media
                      </Label>
                      <div className="grid grid-cols-3 gap-2">
                        {Object.entries(PLATFORM_CONFIG).map(
                          ([key, config]) => (
                            <Button
                              key={key}
                              variant="outline"
                              size="sm"
                              className={`${config.bg} ${config.color} hover:opacity-80 text-xs`}
                              onClick={() => postToSocial(key)}
                            >
                              <Send className="w-3 h-3 mr-1" />
                              {config.label}
                            </Button>
                          )
                        )}
                      </div>

                      {/* Post History */}
                      {clipPosts.length > 0 && (
                        <div className="space-y-2 mt-2">
                          <p className="text-xs text-zinc-500 font-medium">
                            Post History
                          </p>
                          {clipPosts.map((post) => {
                            const pConfig =
                              PLATFORM_CONFIG[post.platform] ||
                              PLATFORM_CONFIG.tiktok;
                            return (
                              <div
                                key={post.id}
                                className="flex items-center justify-between p-2 bg-zinc-800/50 rounded-lg"
                              >
                                <div className="flex items-center gap-2">
                                  <span
                                    className={`text-xs font-medium ${pConfig.color}`}
                                  >
                                    {pConfig.label}
                                  </span>
                                  <Badge
                                    variant="outline"
                                    className={`text-[10px] ${
                                      post.status === "posted"
                                        ? "text-emerald-400 border-emerald-500/30"
                                        : post.status === "failed"
                                          ? "text-red-400 border-red-500/30"
                                          : "text-amber-400 border-amber-500/30"
                                    }`}
                                  >
                                    {post.status}
                                  </Badge>
                                </div>
                                {post.post_url && (
                                  <a
                                    href={post.post_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-blue-400 flex items-center gap-1"
                                  >
                                    <ExternalLink className="w-3 h-3" />
                                    View
                                  </a>
                                )}
                                {post.error_message && (
                                  <span className="text-[10px] text-zinc-500 flex items-center gap-1">
                                    <AlertTriangle className="w-3 h-3" />
                                    {post.error_message}
                                  </span>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-12 text-center">
                    <Eye className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                    <p className="text-zinc-400 text-sm">
                      Select a clip to view details and post
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Create Clip Tab */}
        <TabsContent value="create" className="space-y-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <Upload className="w-4 h-4 text-pink-400" />
                Create New Clip
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-zinc-300 text-sm">Title</Label>
                  <Input
                    placeholder="Stream Highlight"
                    value={clipForm.title}
                    onChange={(e) =>
                      setClipForm({ ...clipForm, title: e.target.value })
                    }
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-zinc-300 text-sm">
                    Duration (seconds)
                  </Label>
                  <Input
                    type="number"
                    value={clipForm.duration_seconds}
                    onChange={(e) =>
                      setClipForm({
                        ...clipForm,
                        duration_seconds: parseInt(e.target.value) || 30,
                      })
                    }
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-zinc-300 text-sm">Description</Label>
                <Input
                  placeholder="Describe the moment..."
                  value={clipForm.description}
                  onChange={(e) =>
                    setClipForm({
                      ...clipForm,
                      description: e.target.value,
                    })
                  }
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>

              <div className="bg-zinc-800/50 rounded-lg border border-dashed border-zinc-700 p-8 text-center">
                <Upload className="w-10 h-10 text-zinc-600 mx-auto mb-2" />
                <p className="text-sm text-zinc-400">
                  Clip upload coming soon
                </p>
                <p className="text-xs text-zinc-600 mt-1">
                  For now, create a clip record and mark timestamps from your
                  hype moments.
                </p>
              </div>

              <div className="flex justify-end">
                <Button
                  className="bg-pink-500 hover:bg-pink-600 text-white"
                  onClick={() => createClip()}
                >
                  <Scissors className="w-4 h-4 mr-1" />
                  Create Clip
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
