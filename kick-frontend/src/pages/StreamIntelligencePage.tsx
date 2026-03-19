import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  BarChart3,
  TrendingUp,
  Clock,
  Gamepad2,
  Trophy,
  Users,
  MessageSquare,
  Calendar,
  Star,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface StreamSession {
  id: string;
  channel: string;
  started_at: string;
  ended_at: string | null;
  duration_minutes: number;
  avg_viewers: number;
  peak_viewers: number;
  new_followers: number;
  messages_count: number;
  unique_chatters: number;
  game: string;
  stream_score: number;
  created_at: string;
}

interface GrowthMetrics {
  channel: string;
  period: string;
  viewer_trend: number;
  follower_trend: number;
  chat_trend: number;
  stream_count: number;
  avg_stream_score: number;
}

interface BestTimeSlot {
  day_of_week: number;
  hour: number;
  score: number;
  avg_viewers: number;
  competition_level: string;
}

interface GamePerformance {
  game: string;
  streams: number;
  avg_viewers: number;
  avg_score: number;
  total_followers: number;
}

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 80 ? "text-emerald-400 bg-emerald-500/20" : score >= 50 ? "text-amber-400 bg-amber-500/20" : "text-red-400 bg-red-500/20";
  return <Badge className={color}>{score}/100</Badge>;
}

function TrendIndicator({ value }: { value: number }) {
  if (value === 0) return <span className="text-zinc-500 text-xs">--</span>;
  const isPositive = value > 0;
  return (
    <span className={`flex items-center text-xs ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
      {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
      {Math.abs(value).toFixed(1)}%
    </span>
  );
}

export function StreamIntelligencePage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [sessions, setSessions] = useState<StreamSession[]>([]);
  const [growth, setGrowth] = useState<GrowthMetrics | null>(null);
  const [bestTimes, setBestTimes] = useState<BestTimeSlot[]>([]);
  const [gamePerf, setGamePerf] = useState<GamePerformance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!channel) return;
    setLoading(true);
    Promise.all([
      api<StreamSession[]>(`/api/intelligence/sessions/${channel}`).then(setSessions),
      api<GrowthMetrics>(`/api/intelligence/growth/${channel}`).then(setGrowth),
      api<BestTimeSlot[]>(`/api/intelligence/best-times/${channel}`).then(setBestTimes),
      api<GamePerformance[]>(`/api/intelligence/game-performance/${channel}`).then(setGamePerf),
    ])
      .catch(() => toast.error("Failed to load intelligence data"))
      .finally(() => setLoading(false));
  }, [channel]);

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
            <BarChart3 className="w-6 h-6 text-emerald-400" />
            Stream Intelligence
          </h2>
          <p className="text-sm text-zinc-500">Your stream performance analytics and growth insights</p>
        </div>
      </div>

      {/* Growth Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs text-zinc-500 uppercase">Streams (30d)</div>
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white mt-1">{growth?.stream_count || 0}</div>
            <TrendIndicator value={growth?.viewer_trend || 0} />
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs text-zinc-500 uppercase">Avg Stream Score</div>
              <Star className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-white mt-1">{growth?.avg_stream_score || 0}</div>
            <span className="text-xs text-zinc-500">out of 100</span>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs text-zinc-500 uppercase">Follower Growth</div>
              <Users className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white mt-1">
              {growth?.follower_trend !== undefined ? `${growth.follower_trend >= 0 ? "+" : ""}${growth.follower_trend.toFixed(1)}%` : "--"}
            </div>
            <TrendIndicator value={growth?.follower_trend || 0} />
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs text-zinc-500 uppercase">Chat Activity</div>
              <MessageSquare className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-white mt-1">
              {growth?.chat_trend !== undefined ? `${growth.chat_trend >= 0 ? "+" : ""}${growth.chat_trend.toFixed(1)}%` : "--"}
            </div>
            <TrendIndicator value={growth?.chat_trend || 0} />
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="sessions" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="sessions" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Calendar className="w-4 h-4 mr-2" />
            Stream History
          </TabsTrigger>
          <TabsTrigger value="best-times" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Clock className="w-4 h-4 mr-2" />
            Best Times
          </TabsTrigger>
          <TabsTrigger value="games" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Gamepad2 className="w-4 h-4 mr-2" />
            Game Performance
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sessions" className="space-y-4 mt-4">
          {sessions.length === 0 ? (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <BarChart3 className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">No stream sessions recorded yet. Sessions are tracked automatically when you stream.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <Card key={session.id} className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">
                            {new Date(session.started_at).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}
                          </span>
                          {session.game && <Badge variant="outline" className="border-zinc-700 text-zinc-400 text-[10px]">{session.game}</Badge>}
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-xs text-zinc-500">
                          <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{session.duration_minutes}m</span>
                          <span className="flex items-center gap-1"><Users className="w-3 h-3" />{session.avg_viewers} avg</span>
                          <span className="flex items-center gap-1"><Trophy className="w-3 h-3" />{session.peak_viewers} peak</span>
                          <span className="flex items-center gap-1"><MessageSquare className="w-3 h-3" />{session.messages_count} msgs</span>
                          <span className="flex items-center gap-1"><TrendingUp className="w-3 h-3" />+{session.new_followers} followers</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="text-right mr-2">
                          <div className="text-xs text-zinc-500">Score</div>
                        </div>
                        <ScoreBadge score={session.stream_score} />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="best-times" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Clock className="w-5 h-5 text-emerald-400" />
                Best Times to Stream
              </CardTitle>
            </CardHeader>
            <CardContent>
              {bestTimes.length === 0 ? (
                <p className="text-zinc-500 text-center py-4">Not enough stream data yet to recommend best times. Keep streaming!</p>
              ) : (
                <div className="space-y-2">
                  {bestTimes.map((slot, i) => (
                    <div key={`${slot.day_of_week}-${slot.hour}`} className="flex items-center gap-4 p-3 rounded-lg bg-zinc-800/50">
                      <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm">
                        {i + 1}
                      </div>
                      <div className="flex-1">
                        <span className="text-white font-medium">{DAY_NAMES[slot.day_of_week]}s at {slot.hour}:00</span>
                        <div className="text-xs text-zinc-500 mt-0.5">{slot.avg_viewers} avg viewers</div>
                      </div>
                      <Badge className={
                        slot.competition_level === "low" ? "bg-emerald-500/20 text-emerald-400" :
                        slot.competition_level === "medium" ? "bg-amber-500/20 text-amber-400" :
                        "bg-red-500/20 text-red-400"
                      }>
                        {slot.competition_level} competition
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="games" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Gamepad2 className="w-5 h-5 text-emerald-400" />
                Game Performance Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              {gamePerf.length === 0 ? (
                <p className="text-zinc-500 text-center py-4">No game data recorded yet. Game performance is tracked from your stream sessions.</p>
              ) : (
                <div className="space-y-2">
                  {gamePerf.map((game) => (
                    <div key={game.game} className="flex items-center gap-4 p-3 rounded-lg bg-zinc-800/50">
                      <Gamepad2 className="w-5 h-5 text-zinc-400" />
                      <div className="flex-1">
                        <span className="text-white font-medium">{game.game}</span>
                        <div className="flex items-center gap-3 mt-1 text-xs text-zinc-500">
                          <span>{game.streams} streams</span>
                          <span>{game.avg_viewers} avg viewers</span>
                          <span>+{game.total_followers} followers</span>
                        </div>
                      </div>
                      <ScoreBadge score={Math.round(game.avg_score)} />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
