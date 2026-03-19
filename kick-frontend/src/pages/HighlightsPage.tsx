import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import {
  Zap,
  Flame,
  Laugh,
  Target,
  Heart,
  AlertTriangle,
  Clock,
  MessageSquare,
  Trash2,
  Star,
  TrendingUp,
  RefreshCw,
  Search,
} from "lucide-react";

interface HighlightMarker {
  id: string;
  channel: string;
  session_id: string | null;
  timestamp_offset_seconds: number;
  intensity: number;
  message_rate: number;
  duration_seconds: number;
  description: string;
  sample_messages: string[];
  category: string;
  created_at: string;
}

interface HighlightSummary {
  channel: string;
  session_id: string | null;
  total_highlights: number;
  peak_moment: HighlightMarker | null;
  highlights: HighlightMarker[];
  stream_summary: string;
}

const CATEGORY_CONFIG: Record<string, { icon: typeof Zap; color: string; bg: string; label: string }> = {
  hype: { icon: Flame, color: "text-orange-400", bg: "bg-orange-500/10", label: "Hype" },
  funny: { icon: Laugh, color: "text-amber-400", bg: "bg-amber-500/10", label: "Funny" },
  clutch: { icon: Target, color: "text-emerald-400", bg: "bg-emerald-500/10", label: "Clutch" },
  fail: { icon: AlertTriangle, color: "text-red-400", bg: "bg-red-500/10", label: "Fail" },
  emotional: { icon: Heart, color: "text-pink-400", bg: "bg-pink-500/10", label: "Emotional" },
};

function formatTimestamp(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function IntensityBar({ intensity }: { intensity: number }) {
  const color = intensity >= 90 ? "bg-red-500" : intensity >= 70 ? "bg-orange-500" : intensity >= 50 ? "bg-amber-500" : "bg-blue-500";
  return (
    <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
      <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${intensity}%` }} />
    </div>
  );
}

export function HighlightsPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [summary, setSummary] = useState<HighlightSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const data = await api<HighlightSummary>(`/api/highlights/summary/${channel}`);
      setSummary(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load highlights");
    } finally {
      setLoading(false);
    }
  }, [channel]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  const detectHypeMoments = async () => {
    setDetecting(true);
    try {
      const result = await api<{ moments_detected: number }>(
        `/api/highlights/detect/${channel}`,
        { method: "POST" }
      );
      toast.success(`Detected ${result.moments_detected} hype moment(s)!`);
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to detect hype moments");
    } finally {
      setDetecting(false);
    }
  };

  const deleteHighlight = async (id: string) => {
    try {
      await api(`/api/highlights/${id}`, { method: "DELETE" });
      toast.success("Highlight removed");
      fetchData();
    } catch {
      toast.error("Failed to delete highlight");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const categoryCount: Record<string, number> = {};
  summary?.highlights.forEach((h) => {
    categoryCount[h.category] = (categoryCount[h.category] || 0) + 1;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-orange-500/20 via-red-500/10 to-transparent border border-orange-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-6 h-6 text-orange-400" />
              <h2 className="text-2xl font-bold text-white">Auto-Highlight Detection</h2>
              <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/30 text-[10px] uppercase font-bold">
                Pro
              </Badge>
            </div>
            <p className="text-zinc-400">
              Automatically detect hype moments from chat activity spikes. Find your best clip-worthy timestamps.
            </p>
          </div>
          <Button
            onClick={detectHypeMoments}
            disabled={detecting}
            className="bg-orange-500 hover:bg-orange-600 text-black"
          >
            {detecting ? (
              <RefreshCw className="w-4 h-4 animate-spin mr-1" />
            ) : (
              <Search className="w-4 h-4 mr-1" />
            )}
            Detect Hype Moments
          </Button>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <Zap className="w-32 h-32 text-orange-500" />
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <Zap className="w-5 h-5 text-orange-400 mb-2" />
            <p className="text-2xl font-bold text-white">{summary?.total_highlights || 0}</p>
            <p className="text-[10px] text-zinc-500 uppercase">Total Highlights</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <Star className="w-5 h-5 text-amber-400 mb-2" />
            <p className="text-2xl font-bold text-white">
              {summary?.peak_moment?.intensity.toFixed(0) || 0}
            </p>
            <p className="text-[10px] text-zinc-500 uppercase">Peak Intensity</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <MessageSquare className="w-5 h-5 text-blue-400 mb-2" />
            <p className="text-2xl font-bold text-white">
              {summary?.peak_moment?.message_rate.toFixed(1) || 0}
            </p>
            <p className="text-[10px] text-zinc-500 uppercase">Peak msg/sec</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <TrendingUp className="w-5 h-5 text-emerald-400 mb-2" />
            <div className="flex items-center gap-1 flex-wrap mt-1">
              {Object.entries(categoryCount).map(([cat, count]) => {
                const cfg = CATEGORY_CONFIG[cat] || CATEGORY_CONFIG.hype;
                return (
                  <Badge key={cat} className={`${cfg.bg} ${cfg.color} text-[9px]`}>
                    {count} {cfg.label}
                  </Badge>
                );
              })}
            </div>
            <p className="text-[10px] text-zinc-500 uppercase mt-1">Categories</p>
          </CardContent>
        </Card>
      </div>

      {/* Stream Summary */}
      {summary?.stream_summary && (
        <Card className="bg-zinc-900/30 border-zinc-800/50">
          <CardContent className="p-4">
            <p className="text-sm text-zinc-300">{summary.stream_summary}</p>
          </CardContent>
        </Card>
      )}

      {/* Highlights List */}
      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <Flame className="w-4 h-4 text-orange-400" />
            Highlight Moments
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[500px]">
            <div className="space-y-1 p-4">
              {summary?.highlights.map((h) => {
                const cfg = CATEGORY_CONFIG[h.category] || CATEGORY_CONFIG.hype;
                const CatIcon = cfg.icon;
                return (
                  <Card key={h.id} className="bg-zinc-900/30 border-zinc-800/50">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                          <div className={`w-10 h-10 rounded-lg ${cfg.bg} flex items-center justify-center shrink-0`}>
                            <CatIcon className={`w-5 h-5 ${cfg.color}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <p className="text-sm font-medium text-white">{h.description}</p>
                              <Badge className={`${cfg.bg} ${cfg.color} text-[10px]`}>{cfg.label}</Badge>
                            </div>
                            <div className="flex items-center gap-3 text-[11px] text-zinc-500 mb-2">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {formatTimestamp(h.timestamp_offset_seconds)}
                              </span>
                              <span className="flex items-center gap-1">
                                <MessageSquare className="w-3 h-3" />
                                {h.message_rate.toFixed(1)} msg/sec
                              </span>
                              <span className="flex items-center gap-1">
                                <Zap className="w-3 h-3" />
                                {h.duration_seconds}s duration
                              </span>
                            </div>
                            <IntensityBar intensity={h.intensity} />
                            {h.sample_messages.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {h.sample_messages.slice(0, 3).map((msg, i) => (
                                  <span key={i} className="text-[10px] text-zinc-500 bg-zinc-800/50 px-2 py-0.5 rounded">
                                    &quot;{msg}&quot;
                                  </span>
                                ))}
                                {h.sample_messages.length > 3 && (
                                  <span className="text-[10px] text-zinc-600">
                                    +{h.sample_messages.length - 3} more
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2 ml-2">
                          <span className="text-lg font-bold text-white">{h.intensity.toFixed(0)}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-zinc-600 hover:text-red-400"
                            onClick={() => deleteHighlight(h.id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
              {(!summary?.highlights || summary.highlights.length === 0) && (
                <div className="text-center py-8">
                  <Zap className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                  <p className="text-zinc-400 text-sm">No highlights detected yet</p>
                  <p className="text-zinc-600 text-xs mt-1">
                    Highlights are automatically generated from chat activity spikes during streams
                  </p>
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
