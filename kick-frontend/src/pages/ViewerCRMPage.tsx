import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  Users,
  UserCheck,
  UserX,
  Heart,
  Search,
  AlertTriangle,
  Megaphone,
  Eye,
  MessageSquare,
  Clock,
  Star,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface ViewerProfile {
  id: string;
  channel: string;
  username: string;
  first_seen: string;
  last_seen: string;
  total_messages: number;
  total_watch_minutes: number;
  streams_attended: number;
  is_subscriber: boolean;
  is_follower: boolean;
  is_moderator: boolean;
  segment: string;
  notes: string;
}

interface SegmentSummary {
  segment: string;
  count: number;
  avg_messages: number;
  avg_watch_minutes: number;
}

interface ChurnRisk {
  username: string;
  channel: string;
  last_seen: string;
  days_absent: number;
  previous_frequency: string;
  risk_level: string;
  total_messages: number;
  streams_attended: number;
}

interface ShoutoutSuggestion {
  username: string;
  reason: string;
  streams_attended: number;
  total_messages: number;
}

const SEGMENT_COLORS: Record<string, string> = {
  new: "bg-blue-500/20 text-blue-400",
  regular: "bg-emerald-500/20 text-emerald-400",
  superfan: "bg-amber-500/20 text-amber-400",
  at_risk: "bg-orange-500/20 text-orange-400",
  churned: "bg-red-500/20 text-red-400",
};

const SEGMENT_ICONS: Record<string, typeof Users> = {
  new: UserCheck,
  regular: Users,
  superfan: Star,
  at_risk: AlertTriangle,
  churned: UserX,
};

export function ViewerCRMPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [viewers, setViewers] = useState<ViewerProfile[]>([]);
  const [total, setTotal] = useState(0);
  const [segments, setSegments] = useState<SegmentSummary[]>([]);
  const [churnRisks, setChurnRisks] = useState<ChurnRisk[]>([]);
  const [shoutouts, setShoutouts] = useState<ShoutoutSuggestion[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeSegment, setActiveSegment] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!channel) return;
    setLoading(true);
    Promise.all([
      api<{ viewers: ViewerProfile[]; total: number }>(`/api/crm/viewers/${channel}`).then((d) => {
        setViewers(d.viewers);
        setTotal(d.total);
      }),
      api<SegmentSummary[]>(`/api/crm/segments/${channel}`).then(setSegments),
      api<ChurnRisk[]>(`/api/crm/churn-risks/${channel}`).then(setChurnRisks),
      api<ShoutoutSuggestion[]>(`/api/crm/shoutouts/${channel}`).then(setShoutouts),
    ])
      .catch(() => toast.error("Failed to load CRM data"))
      .finally(() => setLoading(false));
  }, [channel]);

  const loadViewers = async (segment?: string | null) => {
    try {
      const segParam = segment ? `&segment=${segment}` : "";
      const data = await api<{ viewers: ViewerProfile[]; total: number }>(
        `/api/crm/viewers/${channel}?sort_by=last_seen${segParam}`
      );
      setViewers(data.viewers);
      setTotal(data.total);
    } catch {
      toast.error("Failed to load viewers");
    }
  };

  const filterBySegment = (segment: string | null) => {
    setActiveSegment(segment);
    loadViewers(segment);
  };

  const filteredViewers = searchQuery
    ? viewers.filter((v) => v.username.toLowerCase().includes(searchQuery.toLowerCase()))
    : viewers;

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
            <Heart className="w-6 h-6 text-pink-400" />
            Viewer CRM
          </h2>
          <p className="text-sm text-zinc-500">Know your community — track, segment, and engage your viewers</p>
        </div>
        <Badge className="bg-zinc-800 text-zinc-400">{total} total viewers</Badge>
      </div>

      {/* Segment Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {segments.map((seg) => {
          const SegIcon = SEGMENT_ICONS[seg.segment] || Users;
          return (
            <Card
              key={seg.segment}
              className={`bg-zinc-900/50 border-zinc-800 cursor-pointer transition-colors ${activeSegment === seg.segment ? "border-emerald-500" : "hover:border-zinc-700"}`}
              onClick={() => filterBySegment(activeSegment === seg.segment ? null : seg.segment)}
            >
              <CardContent className="p-3 text-center">
                <SegIcon className={`w-5 h-5 mx-auto mb-1 ${SEGMENT_COLORS[seg.segment]?.split(" ")[1] || "text-zinc-400"}`} />
                <div className="text-lg font-bold text-white">{seg.count}</div>
                <div className="text-xs text-zinc-500 capitalize">{seg.segment.replace("_", " ")}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Tabs defaultValue="viewers" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="viewers" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Users className="w-4 h-4 mr-2" />
            Viewers
          </TabsTrigger>
          <TabsTrigger value="churn" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <AlertTriangle className="w-4 h-4 mr-2" />
            Churn Risks
          </TabsTrigger>
          <TabsTrigger value="shoutouts" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Megaphone className="w-4 h-4 mr-2" />
            Shoutout Suggestions
          </TabsTrigger>
        </TabsList>

        <TabsContent value="viewers" className="space-y-4 mt-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search viewers..."
              className="bg-zinc-900 border-zinc-800 text-white pl-10"
            />
          </div>

          {filteredViewers.length === 0 ? (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Users className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">No viewer profiles yet. Profiles are built automatically from chat activity.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {filteredViewers.map((viewer) => (
                <Card key={viewer.id} className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center text-white font-bold text-sm">
                      {viewer.username.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-white font-medium">{viewer.username}</span>
                        <Badge className={SEGMENT_COLORS[viewer.segment] || "bg-zinc-700 text-zinc-400"}>
                          {viewer.segment.replace("_", " ")}
                        </Badge>
                        {viewer.is_subscriber && <Badge className="bg-purple-500/20 text-purple-400">Sub</Badge>}
                        {viewer.is_moderator && <Badge className="bg-blue-500/20 text-blue-400">Mod</Badge>}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-xs text-zinc-500">
                        <span className="flex items-center gap-1"><MessageSquare className="w-3 h-3" />{viewer.total_messages} msgs</span>
                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{Math.round(viewer.total_watch_minutes / 60)}h watched</span>
                        <span className="flex items-center gap-1"><Eye className="w-3 h-3" />{viewer.streams_attended} streams</span>
                      </div>
                    </div>
                    <div className="text-right text-xs text-zinc-500">
                      <div>Last seen</div>
                      <div className="text-zinc-400">{new Date(viewer.last_seen).toLocaleDateString()}</div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="churn" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-400" />
                Viewers at Risk of Leaving
              </CardTitle>
            </CardHeader>
            <CardContent>
              {churnRisks.length === 0 ? (
                <p className="text-zinc-500 text-center py-4">No churn risks detected. Your community is healthy!</p>
              ) : (
                <div className="space-y-2">
                  {churnRisks.map((risk) => (
                    <div key={risk.username} className="flex items-center gap-4 p-3 rounded-lg bg-zinc-800/50">
                      <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center">
                        <AlertTriangle className={`w-5 h-5 ${risk.risk_level === "high" ? "text-red-400" : "text-orange-400"}`} />
                      </div>
                      <div className="flex-1">
                        <span className="text-white font-medium">{risk.username}</span>
                        <div className="text-xs text-zinc-500 mt-0.5">
                          {risk.streams_attended} streams attended, {risk.total_messages} messages
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge className={risk.risk_level === "high" ? "bg-red-500/20 text-red-400" : "bg-orange-500/20 text-orange-400"}>
                          {risk.risk_level} risk
                        </Badge>
                        <div className="text-xs text-zinc-500 mt-1">Absent {risk.days_absent}d</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="shoutouts" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Megaphone className="w-5 h-5 text-amber-400" />
                Viewers Who Deserve a Shoutout
              </CardTitle>
            </CardHeader>
            <CardContent>
              {shoutouts.length === 0 ? (
                <p className="text-zinc-500 text-center py-4">Not enough viewer data yet for shoutout suggestions.</p>
              ) : (
                <div className="space-y-2">
                  {shoutouts.map((s) => (
                    <div key={s.username} className="flex items-center gap-4 p-3 rounded-lg bg-zinc-800/50">
                      <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
                        <Star className="w-5 h-5 text-amber-400" />
                      </div>
                      <div className="flex-1">
                        <span className="text-white font-medium">{s.username}</span>
                        <div className="text-xs text-zinc-500 mt-0.5">{s.reason}</div>
                      </div>
                      <Button size="sm" variant="outline" className="border-zinc-700 text-zinc-400 hover:text-white">
                        <Megaphone className="w-3 h-3 mr-1" />
                        Shoutout
                      </Button>
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
