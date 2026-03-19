import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { Target, Plus, Trash2, CheckCircle, XCircle, Play } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface GameChallenge {
  id: string;
  channel: string;
  title: string;
  description: string;
  reward_points: number;
  creator_username: string;
  status: string;
  created_at: string;
}

export function GameChallengesPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [challenges, setChallenges] = useState<GameChallenge[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newCh, setNewCh] = useState({ title: "", description: "", reward_points: 100, creator_username: "" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<GameChallenge[]>(`/api/game-challenges/${channel}`)
      .then(setChallenges)
      .catch(() => toast.error("Failed to load challenges"))
      .finally(() => setLoading(false));
  }, [channel]);

  const createChallenge = async () => {
    try {
      const result = await api<GameChallenge>(`/api/game-challenges/${channel}`, {
        method: "POST",
        body: JSON.stringify(newCh),
      });
      setChallenges([result, ...challenges]);
      setNewCh({ title: "", description: "", reward_points: 100, creator_username: "" });
      setShowAdd(false);
      toast.success("Challenge created");
    } catch {
      toast.error("Failed to create");
    }
  };

  const updateStatus = async (id: string, action: string) => {
    try {
      const result = await api<GameChallenge>(`/api/game-challenges/${channel}/${id}/${action}`, { method: "POST" });
      setChallenges(challenges.map((c) => (c.id === id ? result : c)));
      toast.success(`Challenge ${action}ed`);
    } catch {
      toast.error("Failed to update");
    }
  };

  const deleteChallenge = async (id: string) => {
    try {
      await api(`/api/game-challenges/${channel}/${id}`, { method: "DELETE" });
      setChallenges(challenges.filter((c) => c.id !== id));
      toast.success("Deleted");
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

  const statusColor: Record<string, string> = {
    pending: "border-amber-500/30 text-amber-400",
    accepted: "border-blue-500/30 text-blue-400",
    completed: "border-emerald-500/30 text-emerald-400",
    failed: "border-red-500/30 text-red-400",
    rejected: "border-zinc-700 text-zinc-500",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Target className="w-6 h-6 text-orange-400" />
            Game Challenges
          </h2>
          <p className="text-sm text-zinc-500">Viewers create challenges for you to complete</p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
          <Plus className="w-4 h-4 mr-2" /> New Challenge
        </Button>
      </div>

      {showAdd && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardContent className="p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-zinc-400 text-xs">Title</Label>
                <Input value={newCh.title} onChange={(e) => setNewCh({ ...newCh, title: e.target.value })} placeholder="Ace the round" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Reward Points</Label>
                <Input type="number" value={newCh.reward_points} onChange={(e) => setNewCh({ ...newCh, reward_points: parseInt(e.target.value) || 0 })} className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
            </div>
            <div>
              <Label className="text-zinc-400 text-xs">Description</Label>
              <Input value={newCh.description} onChange={(e) => setNewCh({ ...newCh, description: e.target.value })} placeholder="Get 5 kills in one round" className="bg-zinc-800 border-zinc-700 text-white" />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" onClick={() => setShowAdd(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={createChallenge} className="bg-emerald-500 hover:bg-emerald-600 text-black">Create</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {challenges.map((ch) => (
          <Card key={ch.id} className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 flex items-start gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-white font-medium">{ch.title}</h3>
                  <Badge variant="outline" className={`text-[10px] ${statusColor[ch.status] || "border-zinc-700 text-zinc-500"}`}>
                    {ch.status}
                  </Badge>
                  <Badge variant="outline" className="text-[10px] border-amber-500/30 text-amber-400">
                    {ch.reward_points} pts
                  </Badge>
                </div>
                {ch.description && <p className="text-xs text-zinc-500">{ch.description}</p>}
                {ch.creator_username && <p className="text-[10px] text-zinc-600 mt-1">by {ch.creator_username}</p>}
              </div>
              <div className="flex gap-1">
                {ch.status === "pending" && (
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-blue-400" onClick={() => updateStatus(ch.id, "accept")} title="Accept">
                    <Play className="w-3.5 h-3.5" />
                  </Button>
                )}
                {ch.status === "accepted" && (
                  <>
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-emerald-400" onClick={() => updateStatus(ch.id, "complete")} title="Complete">
                      <CheckCircle className="w-3.5 h-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-red-400" onClick={() => updateStatus(ch.id, "fail")} title="Fail">
                      <XCircle className="w-3.5 h-3.5" />
                    </Button>
                  </>
                )}
                <Button variant="ghost" size="icon" className="h-7 w-7 text-zinc-600 hover:text-red-400" onClick={() => deleteChallenge(ch.id)}>
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {challenges.length === 0 && <p className="text-center text-zinc-600 py-8">No challenges yet.</p>}
      </div>
    </div>
  );
}
