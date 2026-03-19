import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { Award, Plus, Trash2, Unlock } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface Achievement {
  id: string;
  channel: string;
  game: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlocked_at: string | null;
}

export function AchievementsPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newAch, setNewAch] = useState({ game: "", title: "", description: "", icon: "" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<Achievement[]>(`/api/achievements/${channel}`)
      .then(setAchievements)
      .catch(() => toast.error("Failed to load achievements"))
      .finally(() => setLoading(false));
  }, [channel]);

  const createAchievement = async () => {
    try {
      const result = await api<Achievement>(`/api/achievements/${channel}`, {
        method: "POST",
        body: JSON.stringify(newAch),
      });
      setAchievements([...achievements, result]);
      setNewAch({ game: "", title: "", description: "", icon: "" });
      setShowAdd(false);
      toast.success("Achievement created");
    } catch {
      toast.error("Failed to create");
    }
  };

  const unlockAchievement = async (id: string) => {
    try {
      const result = await api<Achievement>(`/api/achievements/${channel}/${id}/unlock`, { method: "POST" });
      setAchievements(achievements.map((a) => (a.id === id ? result : a)));
      toast.success("Achievement unlocked!");
    } catch {
      toast.error("Failed to unlock");
    }
  };

  const deleteAchievement = async (id: string) => {
    try {
      await api(`/api/achievements/${channel}/${id}`, { method: "DELETE" });
      setAchievements(achievements.filter((a) => a.id !== id));
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

  const unlocked = achievements.filter((a) => a.unlocked).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Award className="w-6 h-6 text-amber-400" />
            Achievements
          </h2>
          <p className="text-sm text-zinc-500">{unlocked} / {achievements.length} unlocked</p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
          <Plus className="w-4 h-4 mr-2" /> Add Achievement
        </Button>
      </div>

      {showAdd && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardContent className="p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-zinc-400 text-xs">Title</Label>
                <Input value={newAch.title} onChange={(e) => setNewAch({ ...newAch, title: e.target.value })} placeholder="First Blood" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Game</Label>
                <Input value={newAch.game} onChange={(e) => setNewAch({ ...newAch, game: e.target.value })} placeholder="Valorant" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
            </div>
            <div>
              <Label className="text-zinc-400 text-xs">Description</Label>
              <Input value={newAch.description} onChange={(e) => setNewAch({ ...newAch, description: e.target.value })} placeholder="Get the first kill of the match" className="bg-zinc-800 border-zinc-700 text-white" />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" onClick={() => setShowAdd(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={createAchievement} className="bg-emerald-500 hover:bg-emerald-600 text-black">Create</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {achievements.map((ach) => (
          <Card key={ach.id} className={`bg-zinc-900/50 ${ach.unlocked ? "border-amber-500/20" : "border-zinc-800 opacity-60"}`}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-white font-medium">{ach.title}</h3>
                  <p className="text-xs text-zinc-500 mt-1">{ach.description}</p>
                  {ach.game && <Badge variant="outline" className="mt-2 text-[10px] border-zinc-700 text-zinc-400">{ach.game}</Badge>}
                  {ach.unlocked && <Badge className="mt-2 ml-1 text-[10px] bg-amber-500/20 text-amber-400">Unlocked</Badge>}
                </div>
                <div className="flex gap-1">
                  {!ach.unlocked && (
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-amber-400" onClick={() => unlockAchievement(ach.id)}>
                      <Unlock className="w-3.5 h-3.5" />
                    </Button>
                  )}
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-zinc-600 hover:text-red-400" onClick={() => deleteAchievement(ach.id)}>
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        {achievements.length === 0 && (
          <p className="text-center text-zinc-600 py-8 col-span-full">No achievements yet. Add some to track your progress.</p>
        )}
      </div>
    </div>
  );
}
