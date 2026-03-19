import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import {
  Users,
  UserCheck,
  UserX,
  UserPlus,
  Star,
  Heart,
  AlertTriangle,
  Search,
  MessageSquare,
  Clock,
  Gamepad2,
  Megaphone,
  Eye,
} from "lucide-react";

interface ViewerProfile {
  id: string;
  channel: string;
  username: string;
  first_seen: string;
  last_seen: string;
  total_messages: number;
  streams_watched: number;
  is_subscriber: boolean;
  is_follower: boolean;
  segment: string;
  watch_time_minutes: number;
  favorite_games: string[];
  notes: string;
}

interface SegmentSummary {
  segment: string;
  count: number;
  avg_messages: number;
  avg_streams_watched: number;
}

interface ChurnPrediction {
  username: string;
  last_seen: string;
  streams_watched: number;
  risk_level: string;
  suggestion: string;
}

interface CRMOverview {
  channel: string;
  total_viewers: number;
  segments: SegmentSummary[];
  top_viewers: ViewerProfile[];
  at_risk_viewers: ViewerProfile[];
  shoutout_suggestions: ViewerProfile[];
  churn_predictions: ChurnPrediction[];
}

const SEGMENT_CONFIG: Record<string, { icon: typeof Star; color: string; bg: string; label: string }> = {
  super_fan: { icon: Star, color: "text-amber-400", bg: "bg-amber-500/10", label: "Super Fan" },
  regular: { icon: UserCheck, color: "text-blue-400", bg: "bg-blue-500/10", label: "Regular" },
  new: { icon: UserPlus, color: "text-emerald-400", bg: "bg-emerald-500/10", label: "New" },
  at_risk: { icon: AlertTriangle, color: "text-red-400", bg: "bg-red-500/10", label: "At Risk" },
  churned: { icon: UserX, color: "text-zinc-400", bg: "bg-zinc-500/10", label: "Churned" },
};

function ViewerCard({ viewer, onUpdate }: { viewer: ViewerProfile; onUpdate: () => void }) {
  const [editing, setEditing] = useState(false);
  const [notes, setNotes] = useState(viewer.notes);
  const seg = SEGMENT_CONFIG[viewer.segment] || SEGMENT_CONFIG.new;
  const SegIcon = seg.icon;

  const saveNotes = async () => {
    try {
      await api(`/api/viewer-crm/viewer/${viewer.channel}/${viewer.username}`, {
        method: "PUT",
        body: JSON.stringify({ notes }),
      });
      toast.success("Notes updated");
      setEditing(false);
      onUpdate();
    } catch {
      toast.error("Failed to update notes");
    }
  };

  const daysSinceLastSeen = Math.floor(
    (Date.now() - new Date(viewer.last_seen).getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <Card className="bg-zinc-900/30 border-zinc-800/50">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full ${seg.bg} flex items-center justify-center`}>
              <SegIcon className={`w-5 h-5 ${seg.color}`} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="font-medium text-white">{viewer.username}</p>
                <Badge className={`${seg.bg} ${seg.color} text-[10px]`}>{seg.label}</Badge>
                {viewer.is_subscriber && (
                  <Badge className="bg-violet-500/20 text-violet-400 text-[10px]">Sub</Badge>
                )}
              </div>
              <div className="flex items-center gap-3 mt-1 text-[11px] text-zinc-500">
                <span className="flex items-center gap-1">
                  <MessageSquare className="w-3 h-3" />
                  {viewer.total_messages.toLocaleString()} msgs
                </span>
                <span className="flex items-center gap-1">
                  <Eye className="w-3 h-3" />
                  {viewer.streams_watched} streams
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {Math.floor(viewer.watch_time_minutes / 60)}h watched
                </span>
              </div>
            </div>
          </div>
          <div className="text-right text-[11px] text-zinc-500">
            <p>Last seen: {daysSinceLastSeen === 0 ? "Today" : `${daysSinceLastSeen}d ago`}</p>
            <p>Since: {new Date(viewer.first_seen).toLocaleDateString()}</p>
          </div>
        </div>
        {viewer.favorite_games.length > 0 && (
          <div className="flex items-center gap-1 mt-2">
            <Gamepad2 className="w-3 h-3 text-zinc-600" />
            {viewer.favorite_games.map((g) => (
              <Badge key={g} variant="outline" className="text-[10px] border-zinc-700 text-zinc-400">
                {g}
              </Badge>
            ))}
          </div>
        )}
        {(viewer.notes || editing) && (
          <div className="mt-2">
            {editing ? (
              <div className="flex gap-2">
                <Input
                  className="bg-zinc-800 border-zinc-700 text-xs flex-1"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add notes..."
                />
                <Button size="sm" onClick={saveNotes} className="text-xs">Save</Button>
                <Button size="sm" variant="ghost" onClick={() => setEditing(false)} className="text-xs">Cancel</Button>
              </div>
            ) : (
              <p
                className="text-xs text-zinc-500 italic cursor-pointer hover:text-zinc-400"
                onClick={() => setEditing(true)}
              >
                {viewer.notes || "Click to add notes..."}
              </p>
            )}
          </div>
        )}
        {!viewer.notes && !editing && (
          <p
            className="text-xs text-zinc-600 mt-2 cursor-pointer hover:text-zinc-500"
            onClick={() => setEditing(true)}
          >
            + Add notes
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export function ViewerCRMPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [overview, setOverview] = useState<CRMOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filteredViewers, setFilteredViewers] = useState<ViewerProfile[]>([]);

  const fetchData = useCallback(async () => {
    try {
      const data = await api<CRMOverview>(`/api/viewer-crm/overview/${channel}`);
      setOverview(data);
      setFilteredViewers(data.top_viewers);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load CRM data");
    } finally {
      setLoading(false);
    }
  }, [channel]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  const filterBySegment = async (segment: string | null) => {
    try {
      const url = segment
        ? `/api/viewer-crm/viewers/${channel}?segment=${segment}`
        : `/api/viewer-crm/viewers/${channel}`;
      const data = await api<ViewerProfile[]>(url);
      setFilteredViewers(data);
    } catch {
      toast.error("Failed to filter viewers");
    }
  };

  const searchViewers = () => {
    if (!searchQuery.trim()) {
      if (overview) setFilteredViewers(overview.top_viewers);
      return;
    }
    const q = searchQuery.toLowerCase();
    const filtered = (overview?.top_viewers || []).filter(
      (v) => v.username.toLowerCase().includes(q)
    );
    setFilteredViewers(filtered);
  };

  useEffect(() => {
    searchViewers();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-violet-500/20 via-pink-500/10 to-transparent border border-violet-500/20 p-6">
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-1">
            <Heart className="w-6 h-6 text-violet-400" />
            <h2 className="text-2xl font-bold text-white">Viewer CRM</h2>
            <Badge className="bg-violet-500/20 text-violet-400 border-violet-500/30 text-[10px] uppercase font-bold">
              Pro
            </Badge>
          </div>
          <p className="text-zinc-400">
            Know your audience. Track viewer journeys, predict churn, and identify your biggest fans.
          </p>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <Users className="w-32 h-32 text-violet-500" />
        </div>
      </div>

      {/* Segment Summary */}
      {overview && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <Card
            className="bg-zinc-900/50 border-zinc-800 cursor-pointer hover:border-zinc-700"
            onClick={() => filterBySegment(null)}
          >
            <CardContent className="p-4">
              <Users className="w-5 h-5 text-zinc-400 mb-2" />
              <p className="text-2xl font-bold text-white">{overview.total_viewers}</p>
              <p className="text-[10px] text-zinc-500 uppercase">Total Viewers</p>
            </CardContent>
          </Card>
          {overview.segments.map((seg) => {
            const config = SEGMENT_CONFIG[seg.segment] || SEGMENT_CONFIG.new;
            const SegIcon = config.icon;
            return (
              <Card
                key={seg.segment}
                className="bg-zinc-900/50 border-zinc-800 cursor-pointer hover:border-zinc-700"
                onClick={() => filterBySegment(seg.segment)}
              >
                <CardContent className="p-4">
                  <SegIcon className={`w-5 h-5 ${config.color} mb-2`} />
                  <p className="text-2xl font-bold text-white">{seg.count}</p>
                  <p className="text-[10px] text-zinc-500 uppercase">{config.label}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Tabs defaultValue="viewers" className="space-y-4">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="viewers" className="data-[state=active]:bg-zinc-800">
            All Viewers
          </TabsTrigger>
          <TabsTrigger value="at-risk" className="data-[state=active]:bg-zinc-800">
            At Risk
          </TabsTrigger>
          <TabsTrigger value="shoutouts" className="data-[state=active]:bg-zinc-800">
            Shoutout Suggestions
          </TabsTrigger>
          <TabsTrigger value="churn" className="data-[state=active]:bg-zinc-800">
            Churn Predictions
          </TabsTrigger>
        </TabsList>

        {/* All Viewers */}
        <TabsContent value="viewers" className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
              <Input
                className="bg-zinc-900 border-zinc-800 pl-9"
                placeholder="Search viewers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
          <ScrollArea className="h-[600px]">
            <div className="space-y-2">
              {filteredViewers.map((v) => (
                <ViewerCard key={v.id} viewer={v} onUpdate={fetchData} />
              ))}
              {filteredViewers.length === 0 && (
                <div className="text-center py-8">
                  <Users className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                  <p className="text-zinc-400 text-sm">No viewers found</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* At Risk */}
        <TabsContent value="at-risk" className="space-y-4">
          {overview?.at_risk_viewers && overview.at_risk_viewers.length > 0 ? (
            <div className="space-y-2">
              {overview.at_risk_viewers.map((v) => (
                <ViewerCard key={v.id} viewer={v} onUpdate={fetchData} />
              ))}
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <UserCheck className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No at-risk viewers detected</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Shoutouts */}
        <TabsContent value="shoutouts" className="space-y-4">
          <Card className="bg-zinc-900/30 border-zinc-800/50 mb-4">
            <CardContent className="p-4 flex items-center gap-3">
              <Megaphone className="w-5 h-5 text-amber-400" />
              <p className="text-sm text-zinc-400">
                These viewers have been consistently active but haven&apos;t received recognition yet. Consider giving them a shoutout!
              </p>
            </CardContent>
          </Card>
          {overview?.shoutout_suggestions && overview.shoutout_suggestions.length > 0 ? (
            <div className="space-y-2">
              {overview.shoutout_suggestions.map((v) => (
                <ViewerCard key={v.id} viewer={v} onUpdate={fetchData} />
              ))}
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Megaphone className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No shoutout suggestions at this time</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Churn Predictions */}
        <TabsContent value="churn" className="space-y-4">
          {overview?.churn_predictions && overview.churn_predictions.length > 0 ? (
            <div className="space-y-2">
              {overview.churn_predictions.map((p) => (
                <Card key={p.username} className="bg-zinc-900/30 border-zinc-800/50">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className={`w-5 h-5 ${p.risk_level === "high" ? "text-red-400" : "text-amber-400"}`} />
                      <div>
                        <p className="font-medium text-white">{p.username}</p>
                        <p className="text-xs text-zinc-500">
                          Last seen: {new Date(p.last_seen).toLocaleDateString()} |
                          {p.streams_watched} streams watched
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className={`${p.risk_level === "high" ? "bg-red-500/20 text-red-400" : "bg-amber-500/20 text-amber-400"} text-xs`}>
                        {p.risk_level} risk
                      </Badge>
                      <p className="text-xs text-zinc-500 mt-1">{p.suggestion}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <AlertTriangle className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No churn predictions available</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
