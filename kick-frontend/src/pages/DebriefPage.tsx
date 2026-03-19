import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  Brain,
  Sparkles,
  ThumbsUp,
  ThumbsDown,
  Clock,
  Lightbulb,
  TrendingUp,
  MessageSquare,
  Loader2,
  Plus,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface Debrief {
  id: string;
  channel: string;
  session_id: string | null;
  stream_date: string;
  duration_minutes: number;
  summary: string;
  highlights: string[];
  lowlights: string[];
  chat_sentiment_summary: string;
  top_moments: Array<{ timestamp_minutes: number; description: string; intensity: number }>;
  recommendations: string[];
  mood_timeline: Array<{ minute: number; sentiment: number }>;
  status: string;
  created_at: string;
}

export function DebriefPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [debriefs, setDebriefs] = useState<Debrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    if (!channel) return;
    setLoading(true);
    api<Debrief[]>(`/api/debrief/list/${channel}`)
      .then(setDebriefs)
      .catch(() => toast.error("Failed to load debriefs"))
      .finally(() => setLoading(false));
  }, [channel]);

  const createDebrief = async () => {
    setCreating(true);
    try {
      const result = await api<Debrief>("/api/debrief/", {
        method: "POST",
        body: JSON.stringify({
          channel,
          stream_date: new Date().toISOString().split("T")[0],
        }),
      });
      setDebriefs([result, ...debriefs]);
      toast.success("Debrief created — AI analysis will begin shortly");
    } catch {
      toast.error("Failed to create debrief");
    } finally {
      setCreating(false);
    }
  };

  const deleteDebrief = async (id: string) => {
    try {
      await api(`/api/debrief/${id}`, { method: "DELETE" });
      setDebriefs(debriefs.filter((d) => d.id !== id));
      toast.success("Debrief deleted");
    } catch {
      toast.error("Failed to delete debrief");
    }
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Brain className="w-6 h-6 text-purple-400" />
            AI Post-Stream Debrief
          </h2>
          <p className="text-sm text-zinc-500">AI-powered analysis of your streams — highlights, insights, and recommendations</p>
        </div>
        <Button onClick={createDebrief} disabled={creating} className="bg-purple-500 hover:bg-purple-600 text-white">
          {creating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
          New Debrief
        </Button>
      </div>

      {debriefs.length === 0 ? (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-12 text-center">
            <Brain className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">No Debriefs Yet</h3>
            <p className="text-zinc-500 max-w-md mx-auto">
              After your stream ends, create a debrief to get AI-powered insights about what went well,
              what could improve, and actionable recommendations for your next stream.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {debriefs.map((debrief) => {
            const isExpanded = expandedId === debrief.id;
            return (
              <Card key={debrief.id} className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-0">
                  {/* Header - always visible */}
                  <div
                    className="flex items-center justify-between p-4 cursor-pointer hover:bg-zinc-800/30 transition-colors"
                    onClick={() => setExpandedId(isExpanded ? null : debrief.id)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center">
                        <Sparkles className="w-5 h-5 text-purple-400" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">
                            {new Date(debrief.stream_date).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
                          </span>
                          <Badge className={
                            debrief.status === "completed" ? "bg-emerald-500/20 text-emerald-400" :
                            debrief.status === "analyzing" ? "bg-amber-500/20 text-amber-400" :
                            debrief.status === "failed" ? "bg-red-500/20 text-red-400" :
                            "bg-zinc-700/50 text-zinc-400"
                          }>
                            {debrief.status}
                          </Badge>
                        </div>
                        {debrief.duration_minutes > 0 && (
                          <div className="flex items-center gap-1 text-xs text-zinc-500 mt-0.5">
                            <Clock className="w-3 h-3" />
                            {Math.round(debrief.duration_minutes / 60)}h {debrief.duration_minutes % 60}m
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost" size="sm"
                        className="text-zinc-500 hover:text-red-400"
                        onClick={(e) => { e.stopPropagation(); deleteDebrief(debrief.id); }}
                      >
                        Delete
                      </Button>
                      {isExpanded ? <ChevronUp className="w-4 h-4 text-zinc-500" /> : <ChevronDown className="w-4 h-4 text-zinc-500" />}
                    </div>
                  </div>

                  {/* Expanded content */}
                  {isExpanded && (
                    <div className="border-t border-zinc-800 p-4 space-y-4">
                      {/* Summary */}
                      {debrief.summary && (
                        <div>
                          <h4 className="text-sm font-semibold text-zinc-400 uppercase mb-2">Summary</h4>
                          <p className="text-white">{debrief.summary}</p>
                        </div>
                      )}

                      {/* Highlights & Lowlights */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {debrief.highlights.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold text-emerald-400 flex items-center gap-1 mb-2">
                              <ThumbsUp className="w-4 h-4" /> Highlights
                            </h4>
                            <ul className="space-y-1">
                              {debrief.highlights.map((h, i) => (
                                <li key={i} className="text-sm text-zinc-300 pl-4 border-l-2 border-emerald-500/30">{h}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {debrief.lowlights.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold text-red-400 flex items-center gap-1 mb-2">
                              <ThumbsDown className="w-4 h-4" /> Areas to Improve
                            </h4>
                            <ul className="space-y-1">
                              {debrief.lowlights.map((l, i) => (
                                <li key={i} className="text-sm text-zinc-300 pl-4 border-l-2 border-red-500/30">{l}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Chat Sentiment */}
                      {debrief.chat_sentiment_summary && (
                        <div>
                          <h4 className="text-sm font-semibold text-zinc-400 flex items-center gap-1 mb-2">
                            <MessageSquare className="w-4 h-4" /> Chat Sentiment
                          </h4>
                          <p className="text-sm text-zinc-300">{debrief.chat_sentiment_summary}</p>
                        </div>
                      )}

                      {/* Top Moments */}
                      {debrief.top_moments.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-amber-400 flex items-center gap-1 mb-2">
                            <TrendingUp className="w-4 h-4" /> Top Moments
                          </h4>
                          <div className="space-y-2">
                            {debrief.top_moments.map((m, i) => (
                              <div key={i} className="flex items-center gap-3 p-2 rounded bg-zinc-800/50">
                                <Badge className="bg-amber-500/20 text-amber-400 font-mono">
                                  {Math.floor(m.timestamp_minutes / 60)}:{String(m.timestamp_minutes % 60).padStart(2, "0")}
                                </Badge>
                                <span className="text-sm text-zinc-300 flex-1">{m.description}</span>
                                <div className="w-16 h-2 bg-zinc-700 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-amber-400 rounded-full"
                                    style={{ width: `${m.intensity * 100}%` }}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Recommendations */}
                      {debrief.recommendations.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-blue-400 flex items-center gap-1 mb-2">
                            <Lightbulb className="w-4 h-4" /> Recommendations
                          </h4>
                          <ul className="space-y-2">
                            {debrief.recommendations.map((r, i) => (
                              <li key={i} className="flex items-start gap-2 text-sm text-zinc-300">
                                <Lightbulb className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                                {r}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Pending state */}
                      {debrief.status === "pending" && !debrief.summary && (
                        <div className="text-center py-6">
                          <Loader2 className="w-8 h-8 text-purple-400 mx-auto mb-2 animate-spin" />
                          <p className="text-zinc-500">AI is analyzing your stream data...</p>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
