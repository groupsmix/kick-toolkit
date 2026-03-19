import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { TrendingUp, Plus, Trash2 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface RankEntry {
  id: string;
  channel: string;
  game: string;
  current_rank: string;
  peak_rank: string;
  rank_points: number;
  updated_at: string;
}

export function RankTrackerPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [ranks, setRanks] = useState<RankEntry[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newRank, setNewRank] = useState({ game: "", current_rank: "", peak_rank: "", rank_points: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<RankEntry[]>(`/api/rank-tracker/${channel}`)
      .then(setRanks)
      .catch(() => toast.error("Failed to load ranks"))
      .finally(() => setLoading(false));
  }, [channel]);

  const upsertRank = async () => {
    try {
      const result = await api<RankEntry>(`/api/rank-tracker/${channel}`, {
        method: "POST",
        body: JSON.stringify(newRank),
      });
      setRanks([...ranks.filter((r) => r.game !== newRank.game), result]);
      setNewRank({ game: "", current_rank: "", peak_rank: "", rank_points: 0 });
      setShowAdd(false);
      toast.success("Rank updated");
    } catch {
      toast.error("Failed to update rank");
    }
  };

  const deleteRank = async (game: string) => {
    try {
      await api(`/api/rank-tracker/${channel}/${encodeURIComponent(game)}`, { method: "DELETE" });
      setRanks(ranks.filter((r) => r.game !== game));
      toast.success("Rank deleted");
    } catch {
      toast.error("Failed to delete");
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
            <TrendingUp className="w-6 h-6 text-purple-400" />
            Rank Tracker
          </h2>
          <p className="text-sm text-zinc-500">Track your rank progression per game</p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
          <Plus className="w-4 h-4 mr-2" /> Add / Update Rank
        </Button>
      </div>

      {showAdd && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardContent className="p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-zinc-400 text-xs">Game</Label>
                <Input value={newRank.game} onChange={(e) => setNewRank({ ...newRank, game: e.target.value })} placeholder="Valorant" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Current Rank</Label>
                <Input value={newRank.current_rank} onChange={(e) => setNewRank({ ...newRank, current_rank: e.target.value })} placeholder="Diamond 2" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-zinc-400 text-xs">Peak Rank</Label>
                <Input value={newRank.peak_rank} onChange={(e) => setNewRank({ ...newRank, peak_rank: e.target.value })} placeholder="Immortal 1" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Rank Points / LP</Label>
                <Input type="number" value={newRank.rank_points} onChange={(e) => setNewRank({ ...newRank, rank_points: parseInt(e.target.value) || 0 })} className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" onClick={() => setShowAdd(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={upsertRank} className="bg-emerald-500 hover:bg-emerald-600 text-black">Save Rank</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {ranks.map((rank) => (
          <Card key={rank.id} className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <Badge variant="outline" className="text-[10px] border-zinc-700 text-zinc-400 mb-2">{rank.game}</Badge>
                  <p className="text-2xl font-bold text-white">{rank.current_rank}</p>
                  <p className="text-xs text-zinc-500 mt-1">{rank.rank_points} LP/RP</p>
                  {rank.peak_rank && (
                    <p className="text-xs text-amber-400 mt-1">Peak: {rank.peak_rank}</p>
                  )}
                </div>
                <Button variant="ghost" size="icon" className="h-7 w-7 text-zinc-600 hover:text-red-400" onClick={() => deleteRank(rank.game)}>
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {ranks.length === 0 && (
          <p className="text-center text-zinc-600 py-8 col-span-full">No ranks tracked yet.</p>
        )}
      </div>
    </div>
  );
}
