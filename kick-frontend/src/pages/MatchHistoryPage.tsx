import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { Swords, Plus, Trash2, Trophy, TrendingUp } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface MatchRecord {
  id: string;
  channel: string;
  game: string;
  opponent: string;
  result: string;
  score: string;
  notes: string;
  created_at: string;
}

interface MatchStats {
  total: number;
  wins: number;
  losses: number;
  draws: number;
  win_rate: number;
  current_streak: number;
  streak_type: string;
}

export function MatchHistoryPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [matches, setMatches] = useState<MatchRecord[]>([]);
  const [stats, setStats] = useState<MatchStats>({ total: 0, wins: 0, losses: 0, draws: 0, win_rate: 0, current_streak: 0, streak_type: "" });
  const [showAdd, setShowAdd] = useState(false);
  const [newMatch, setNewMatch] = useState({ game: "", opponent: "", result: "win", score: "", notes: "" });
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([
      api<MatchRecord[]>(`/api/match-history/${channel}`),
      api<MatchStats>(`/api/match-history/${channel}/stats`),
    ])
      .then(([m, s]) => { setMatches(m); setStats(s); })
      .catch(() => toast.error("Failed to load match history"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [channel]);

  const addMatch = async () => {
    try {
      await api(`/api/match-history/${channel}`, {
        method: "POST",
        body: JSON.stringify(newMatch),
      });
      setNewMatch({ game: "", opponent: "", result: "win", score: "", notes: "" });
      setShowAdd(false);
      toast.success("Match recorded");
      load();
    } catch {
      toast.error("Failed to add match");
    }
  };

  const deleteMatch = async (id: string) => {
    try {
      await api(`/api/match-history/${channel}/${id}`, { method: "DELETE" });
      toast.success("Match deleted");
      load();
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
            <Swords className="w-6 h-6 text-red-400" />
            Match History
          </h2>
          <p className="text-sm text-zinc-500">Track your W/L record</p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
          <Plus className="w-4 h-4 mr-2" /> Log Match
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-emerald-400">{stats.wins}</p>
            <p className="text-xs text-zinc-500">Wins</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-red-400">{stats.losses}</p>
            <p className="text-xs text-zinc-500">Losses</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4 text-center">
            <Trophy className="w-5 h-5 text-amber-400 mx-auto mb-1" />
            <p className="text-2xl font-bold text-white">{stats.win_rate?.toFixed(0) || 0}%</p>
            <p className="text-xs text-zinc-500">Win Rate</p>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4 text-center">
            <TrendingUp className="w-5 h-5 text-blue-400 mx-auto mb-1" />
            <p className="text-2xl font-bold text-white">{stats.current_streak}</p>
            <p className="text-xs text-zinc-500">{stats.streak_type} Streak</p>
          </CardContent>
        </Card>
      </div>

      {showAdd && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardContent className="p-4 space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label className="text-zinc-400 text-xs">Game</Label>
                <Input value={newMatch.game} onChange={(e) => setNewMatch({ ...newMatch, game: e.target.value })} placeholder="Valorant" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Opponent</Label>
                <Input value={newMatch.opponent} onChange={(e) => setNewMatch({ ...newMatch, opponent: e.target.value })} placeholder="Team Alpha" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Result</Label>
                <select value={newMatch.result} onChange={(e) => setNewMatch({ ...newMatch, result: e.target.value })} className="w-full h-10 rounded-md border border-zinc-700 bg-zinc-800 text-white px-3 text-sm">
                  <option value="win">Win</option>
                  <option value="loss">Loss</option>
                  <option value="draw">Draw</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" onClick={() => setShowAdd(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={addMatch} className="bg-emerald-500 hover:bg-emerald-600 text-black">Log Match</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-white">Recent Matches</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {matches.map((m) => (
              <div key={m.id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/80 border border-zinc-800">
                <div className="flex items-center gap-3">
                  <Badge className={`text-[10px] ${m.result === "win" ? "bg-emerald-500/20 text-emerald-400" : m.result === "loss" ? "bg-red-500/20 text-red-400" : "bg-zinc-500/20 text-zinc-400"}`}>
                    {m.result.toUpperCase()}
                  </Badge>
                  <div>
                    <span className="text-sm text-white">{m.game}</span>
                    {m.opponent && <span className="text-xs text-zinc-500 ml-2">vs {m.opponent}</span>}
                  </div>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-600 hover:text-red-400" onClick={() => deleteMatch(m.id)}>
                  <Trash2 className="w-3 h-3" />
                </Button>
              </div>
            ))}
            {matches.length === 0 && <p className="text-center text-zinc-600 py-4">No matches recorded yet.</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
