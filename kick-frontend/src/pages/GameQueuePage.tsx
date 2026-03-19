import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { Gamepad2, Plus, Users, Shuffle, Lock } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface GameQueue {
  id: string;
  channel: string;
  game: string;
  status: string;
  players: string[];
  max_players: number;
  created_at: string;
}

export function GameQueuePage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [queue, setQueue] = useState<GameQueue | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [game, setGame] = useState("");
  const [maxPlayers, setMaxPlayers] = useState(10);
  const [teams, setTeams] = useState<string[][] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<GameQueue[]>(`/api/game-queue/${channel}`)
      .then((queues) => {
        const active = queues.find((q) => q.status === "open");
        setQueue(active || null);
      })
      .catch(() => toast.error("Failed to load queue"))
      .finally(() => setLoading(false));
  }, [channel]);

  const createQueue = async () => {
    try {
      const result = await api<GameQueue>(`/api/game-queue/${channel}`, {
        method: "POST",
        body: JSON.stringify({ game, max_players: maxPlayers }),
      });
      setQueue(result);
      setShowCreate(false);
      toast.success("Queue created");
    } catch {
      toast.error("Failed to create queue");
    }
  };

  const closeQueue = async () => {
    if (!queue) return;
    try {
      const result = await api<GameQueue>(`/api/game-queue/${channel}/${queue.id}/close`, { method: "POST" });
      setQueue(result);
      toast.success("Queue closed");
    } catch {
      toast.error("Failed to close queue");
    }
  };

  const pickTeams = async (teamCount: number) => {
    if (!queue) return;
    try {
      const result = await api<{ teams: string[][] }>(`/api/game-queue/${channel}/${queue.id}/pick-teams?team_count=${teamCount}`, { method: "POST" });
      setTeams(result.teams);
      toast.success("Teams picked!");
    } catch {
      toast.error("Need more players for teams");
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
            <Gamepad2 className="w-6 h-6 text-purple-400" />
            Game Queue
          </h2>
          <p className="text-sm text-zinc-500">Viewers join the queue to play with you</p>
        </div>
        {!queue && (
          <Button onClick={() => setShowCreate(true)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
            <Plus className="w-4 h-4 mr-2" /> New Queue
          </Button>
        )}
      </div>

      {showCreate && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardContent className="p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-zinc-400 text-xs">Game</Label>
                <Input value={game} onChange={(e) => setGame(e.target.value)} placeholder="Valorant" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Max Players</Label>
                <Input type="number" value={maxPlayers} onChange={(e) => setMaxPlayers(parseInt(e.target.value) || 10)} className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" onClick={() => setShowCreate(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={createQueue} className="bg-emerald-500 hover:bg-emerald-600 text-black">Create</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {queue && (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-white font-medium">{queue.game || "Game Queue"}</h3>
                <Badge variant="outline" className={`text-[10px] ${queue.status === "open" ? "border-emerald-500/30 text-emerald-400" : "border-zinc-700 text-zinc-500"}`}>
                  {queue.status}
                </Badge>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => pickTeams(2)} className="text-xs border-zinc-700 text-zinc-300">
                  <Shuffle className="w-3 h-3 mr-1" /> 2 Teams
                </Button>
                <Button variant="outline" size="sm" onClick={() => pickTeams(4)} className="text-xs border-zinc-700 text-zinc-300">
                  <Shuffle className="w-3 h-3 mr-1" /> 4 Teams
                </Button>
                {queue.status === "open" && (
                  <Button variant="ghost" size="sm" onClick={closeQueue} className="text-red-400 text-xs">
                    <Lock className="w-3 h-3 mr-1" /> Close
                  </Button>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 mb-3">
              <Users className="w-4 h-4 text-zinc-500" />
              <span className="text-sm text-zinc-400">{(queue.players || []).length} / {queue.max_players} players</span>
            </div>

            <div className="flex flex-wrap gap-2">
              {(queue.players || []).map((player, i) => (
                <Badge key={i} variant="outline" className="border-zinc-700 text-zinc-300">{player}</Badge>
              ))}
              {(queue.players || []).length === 0 && <p className="text-sm text-zinc-600">No players yet. Viewers can join with !join</p>}
            </div>
          </CardContent>
        </Card>
      )}

      {teams && (
        <div className="grid grid-cols-2 gap-4">
          {teams.map((team, i) => (
            <Card key={i} className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <h4 className="text-white font-medium mb-2">Team {i + 1}</h4>
                <div className="flex flex-wrap gap-1">
                  {team.map((p) => (
                    <Badge key={p} variant="outline" className="border-emerald-500/30 text-emerald-400">{p}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
