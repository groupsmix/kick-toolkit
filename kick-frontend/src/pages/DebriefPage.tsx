import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
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
} from "recharts";
import {
  Brain,
  Sparkles,
  TrendingUp,
  MessageSquare,
  Lightbulb,
  Tag,
  Zap,
  FileText,
  RefreshCw,
  Clock,
} from "lucide-react";

interface DebriefResult {
  id: string;
  channel: string;
  session_id: string | null;
  summary: string;
  top_moments: { minute: number; description: string; intensity: number }[];
  sentiment_timeline: { minute: number; sentiment: number; label: string }[];
  chat_highlights: string[];
  recommendations: string[];
  title_suggestions: string[];
  trending_topics: string[];
  created_at: string;
}

export function DebriefPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [debriefs, setDebriefs] = useState<DebriefResult[]>([]);
  const [selected, setSelected] = useState<DebriefResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const data = await api<DebriefResult[]>(`/api/debrief/list/${channel}`);
      setDebriefs(data);
      if (data.length > 0 && !selected) {
        setSelected(data[0]);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load debriefs");
    } finally {
      setLoading(false);
    }
  }, [channel, selected]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  const generateDebrief = async () => {
    setGenerating(true);
    try {
      const result = await api<DebriefResult>("/api/debrief/generate", {
        method: "POST",
        body: JSON.stringify({ channel }),
      });
      toast.success("Debrief generated!");
      setSelected(result);
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to generate debrief");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-cyan-500/20 via-blue-500/10 to-transparent border border-cyan-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Brain className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-bold text-white">AI Post-Stream Debrief</h2>
              <Badge className="bg-cyan-500/20 text-cyan-400 border-cyan-500/30 text-[10px] uppercase font-bold">
                Pro
              </Badge>
            </div>
            <p className="text-zinc-400">
              AI-powered analysis of your streams. Understand what worked, what didn&apos;t, and how to improve.
            </p>
          </div>
          <Button
            className="bg-cyan-600 hover:bg-cyan-700"
            onClick={generateDebrief}
            disabled={generating}
          >
            {generating ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4 mr-2" />
            )}
            Generate Debrief
          </Button>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <Brain className="w-32 h-32 text-cyan-500" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Debrief List */}
        <div className="lg:col-span-1">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400">Past Debriefs</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[600px]">
                <div className="space-y-1 p-2">
                  {debriefs.map((d) => (
                    <button
                      key={d.id}
                      className={`w-full text-left p-3 rounded-lg transition-colors ${
                        selected?.id === d.id
                          ? "bg-cyan-500/10 border border-cyan-500/30"
                          : "hover:bg-zinc-800/50"
                      }`}
                      onClick={() => setSelected(d)}
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-cyan-400 shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm text-white truncate">
                            {d.summary.slice(0, 50)}...
                          </p>
                          <p className="text-[10px] text-zinc-500 flex items-center gap-1 mt-0.5">
                            <Clock className="w-3 h-3" />
                            {new Date(d.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                  {debriefs.length === 0 && (
                    <div className="p-4 text-center">
                      <Brain className="w-8 h-8 text-zinc-700 mx-auto mb-2" />
                      <p className="text-xs text-zinc-500">
                        No debriefs yet. Click Generate to create one.
                      </p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Selected Debrief */}
        <div className="lg:col-span-3 space-y-4">
          {selected ? (
            <>
              {/* Summary */}
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    Stream Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-zinc-300 leading-relaxed">{selected.summary}</p>
                </CardContent>
              </Card>

              {/* Sentiment Timeline */}
              {selected.sentiment_timeline.length > 0 && (
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader>
                    <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-emerald-400" />
                      Chat Sentiment Timeline
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={selected.sentiment_timeline}>
                        <defs>
                          <linearGradient id="sentimentGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                        <XAxis
                          dataKey="minute"
                          tick={{ fill: "#71717a", fontSize: 11 }}
                          tickFormatter={(v) => `${v}m`}
                        />
                        <YAxis
                          domain={[0, 1]}
                          tick={{ fill: "#71717a", fontSize: 11 }}
                          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                        />
                        <Tooltip
                          contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
                          labelFormatter={(v) => `Minute ${v}`}
                          formatter={(value: number) => [`${(value * 100).toFixed(0)}%`, "Sentiment"]}
                        />
                        <Area
                          type="monotone"
                          dataKey="sentiment"
                          stroke="#06b6d4"
                          fill="url(#sentimentGrad)"
                          strokeWidth={2}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Top Moments */}
                {selected.top_moments.length > 0 && (
                  <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardHeader>
                      <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                        <Zap className="w-4 h-4 text-amber-400" />
                        Top Moments
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {selected.top_moments.map((m, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="bg-amber-500/10 rounded-full w-8 h-8 flex items-center justify-center shrink-0">
                            <span className="text-xs font-bold text-amber-400">{m.intensity}</span>
                          </div>
                          <div>
                            <p className="text-sm text-white">{m.description}</p>
                            <p className="text-[10px] text-zinc-500">at minute {m.minute}</p>
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}

                {/* Recommendations */}
                {selected.recommendations.length > 0 && (
                  <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardHeader>
                      <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4 text-emerald-400" />
                        Recommendations
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {selected.recommendations.map((r, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <div className="w-5 h-5 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0 mt-0.5">
                            <span className="text-[10px] text-emerald-400">{i + 1}</span>
                          </div>
                          <p className="text-sm text-zinc-300">{r}</p>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Chat Highlights */}
                {selected.chat_highlights.length > 0 && (
                  <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardHeader>
                      <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-blue-400" />
                        Chat Highlights
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {selected.chat_highlights.map((h, i) => (
                        <p key={i} className="text-xs text-zinc-400 bg-zinc-800/50 p-2 rounded">
                          &quot;{h}&quot;
                        </p>
                      ))}
                    </CardContent>
                  </Card>
                )}

                {/* Title Suggestions */}
                {selected.title_suggestions.length > 0 && (
                  <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardHeader>
                      <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                        <Tag className="w-4 h-4 text-violet-400" />
                        Title Ideas
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {selected.title_suggestions.map((t, i) => (
                        <p key={i} className="text-xs text-zinc-300 bg-violet-500/5 p-2 rounded border border-violet-500/10">
                          {t}
                        </p>
                      ))}
                    </CardContent>
                  </Card>
                )}

                {/* Trending Topics */}
                {selected.trending_topics.length > 0 && (
                  <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardHeader>
                      <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-pink-400" />
                        Trending Topics
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {selected.trending_topics.map((t, i) => (
                          <Badge key={i} variant="outline" className="border-pink-500/30 text-pink-400 text-xs">
                            {t}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-12 text-center">
                <Brain className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
                <p className="text-zinc-400">No debrief selected</p>
                <p className="text-zinc-600 text-sm mt-1">
                  Select a debrief from the list or generate a new one
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
