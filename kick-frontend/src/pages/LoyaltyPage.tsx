import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  Star,
  Trophy,
  Gift,
  Plus,
  Trash2,
  Settings,
  Crown,
  Users,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface LeaderboardEntry {
  username: string;
  balance: number;
  total_earned: number;
  watch_time_minutes: number;
  message_count: number;
}

interface Reward {
  id: string;
  channel: string;
  name: string;
  description: string;
  cost: number;
  type: string;
  enabled: boolean;
  max_redemptions: number | null;
  total_redemptions: number;
  created_at: string;
}

interface LoyaltySettings {
  channel: string;
  enabled: boolean;
  points_name: string;
  points_per_message: number;
  points_per_minute_watched: number;
  bonus_subscriber_multiplier: number;
  bonus_follower_multiplier: number;
  daily_bonus: number;
}

export function LoyaltyPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [settings, setSettings] = useState<LoyaltySettings>({
    channel: "",
    enabled: true,
    points_name: "Points",
    points_per_message: 1,
    points_per_minute_watched: 2,
    bonus_subscriber_multiplier: 2.0,
    bonus_follower_multiplier: 1.5,
    daily_bonus: 50,
  });
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [showAddReward, setShowAddReward] = useState(false);
  const [newReward, setNewReward] = useState({ name: "", description: "", cost: 100, type: "custom" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<LoyaltySettings>(`/api/loyalty/settings/${channel}`).then(setSettings),
      api<LeaderboardEntry[]>(`/api/loyalty/leaderboard/${channel}`).then(setLeaderboard),
      api<Reward[]>(`/api/loyalty/rewards/${channel}`).then(setRewards),
    ])
      .catch(() => toast.error("Failed to load loyalty data"))
      .finally(() => setLoading(false));
  }, [channel]);

  const saveSettings = async () => {
    try {
      const result = await api<LoyaltySettings>(`/api/loyalty/settings/${channel}`, {
        method: "POST",
        body: JSON.stringify(settings),
      });
      setSettings(result);
      toast.success("Loyalty settings saved");
    } catch {
      toast.error("Failed to save settings");
    }
  };

  const addReward = async () => {
    if (!newReward.name) return;
    try {
      const result = await api<Reward>(`/api/loyalty/rewards/${channel}`, {
        method: "POST",
        body: JSON.stringify({ ...newReward, enabled: true }),
      });
      setRewards([...rewards, result]);
      setNewReward({ name: "", description: "", cost: 100, type: "custom" });
      setShowAddReward(false);
      toast.success(`Reward "${result.name}" created`);
    } catch {
      toast.error("Failed to create reward");
    }
  };

  const deleteReward = async (id: string) => {
    try {
      await api(`/api/loyalty/rewards/${channel}/${id}`, { method: "DELETE" });
      setRewards(rewards.filter((r) => r.id !== id));
      toast.success("Reward deleted");
    } catch {
      toast.error("Failed to delete reward");
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
            <Star className="w-6 h-6 text-amber-400" />
            Loyalty & Points
          </h2>
          <p className="text-sm text-zinc-500">Reward your viewers for watching and chatting</p>
        </div>
        <Badge className={settings.enabled ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-700/50 text-zinc-400"}>
          {settings.enabled ? "Active" : "Disabled"}
        </Badge>
      </div>

      <Tabs defaultValue="leaderboard" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="leaderboard" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Trophy className="w-4 h-4 mr-2" />
            Leaderboard
          </TabsTrigger>
          <TabsTrigger value="rewards" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Gift className="w-4 h-4 mr-2" />
            Rewards
          </TabsTrigger>
          <TabsTrigger value="settings" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="leaderboard" className="space-y-4 mt-4">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-5 h-5 text-zinc-400" />
            <h3 className="text-lg font-semibold text-white">Top Viewers</h3>
          </div>
          {leaderboard.length === 0 ? (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Trophy className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">No points data yet. Points are earned as viewers watch and chat.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {leaderboard.map((entry, index) => (
                <Card key={entry.username} className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-zinc-800 text-sm font-bold">
                      {index < 3 ? (
                        <Crown className={`w-4 h-4 ${index === 0 ? "text-amber-400" : index === 1 ? "text-zinc-300" : "text-amber-600"}`} />
                      ) : (
                        <span className="text-zinc-500">{index + 1}</span>
                      )}
                    </div>
                    <div className="flex-1">
                      <span className="text-white font-medium">{entry.username}</span>
                      <div className="flex items-center gap-3 mt-1 text-xs text-zinc-500">
                        <span>{entry.message_count} messages</span>
                        <span>{Math.round(entry.watch_time_minutes / 60)}h watched</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-bold text-amber-400">{entry.balance.toLocaleString()}</span>
                      <span className="text-xs text-zinc-500 ml-1">{settings.points_name}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="rewards" className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Rewards Store</h3>
            <Button onClick={() => setShowAddReward(!showAddReward)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
              <Plus className="w-4 h-4 mr-2" />
              Add Reward
            </Button>
          </div>

          {showAddReward && (
            <Card className="bg-zinc-900/50 border-emerald-500/20">
              <CardContent className="p-4 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-zinc-400 text-xs">Reward Name</Label>
                    <Input value={newReward.name} onChange={(e) => setNewReward({ ...newReward, name: e.target.value })} placeholder="VIP Access" className="bg-zinc-800 border-zinc-700 text-white" />
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">Cost ({settings.points_name})</Label>
                    <Input type="number" value={newReward.cost} onChange={(e) => setNewReward({ ...newReward, cost: parseInt(e.target.value) || 0 })} className="bg-zinc-800 border-zinc-700 text-white" />
                  </div>
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Description</Label>
                  <Input value={newReward.description} onChange={(e) => setNewReward({ ...newReward, description: e.target.value })} placeholder="Get VIP status for a day" className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" onClick={() => setShowAddReward(false)} className="text-zinc-400">Cancel</Button>
                  <Button onClick={addReward} className="bg-emerald-500 hover:bg-emerald-600 text-black">Save Reward</Button>
                </div>
              </CardContent>
            </Card>
          )}

          {rewards.length === 0 && !showAddReward ? (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Gift className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">No rewards created yet. Add rewards that viewers can redeem with their points.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {rewards.map((reward) => (
                <Card key={reward.id} className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-white font-medium">{reward.name}</span>
                        <Badge variant="outline" className="text-[10px] border-zinc-700 text-zinc-500">{reward.type}</Badge>
                      </div>
                      <p className="text-sm text-zinc-500 mt-1">{reward.description}</p>
                      <div className="flex items-center gap-3 mt-1 text-xs text-zinc-500">
                        <span>{reward.total_redemptions} redeemed</span>
                        {reward.max_redemptions && <span>Max: {reward.max_redemptions}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className="bg-amber-500/20 text-amber-400">{reward.cost} {settings.points_name}</Badge>
                      <Button variant="ghost" size="icon" className="text-zinc-500 hover:text-red-400" onClick={() => deleteReward(reward.id)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="settings" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Settings className="w-5 h-5 text-emerald-400" />
                Points Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-white">Enable Loyalty System</Label>
                  <p className="text-xs text-zinc-500">Toggle the entire points system on/off</p>
                </div>
                <Switch checked={settings.enabled} onCheckedChange={(v) => setSettings({ ...settings, enabled: v })} />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-zinc-400 text-xs">Points Name</Label>
                  <Input value={settings.points_name} onChange={(e) => setSettings({ ...settings, points_name: e.target.value })} className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Daily Bonus</Label>
                  <Input type="number" value={settings.daily_bonus} onChange={(e) => setSettings({ ...settings, daily_bonus: parseInt(e.target.value) || 0 })} className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Points Per Message</Label>
                  <Input type="number" value={settings.points_per_message} onChange={(e) => setSettings({ ...settings, points_per_message: parseInt(e.target.value) || 0 })} className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Points Per Minute Watched</Label>
                  <Input type="number" value={settings.points_per_minute_watched} onChange={(e) => setSettings({ ...settings, points_per_minute_watched: parseInt(e.target.value) || 0 })} className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Subscriber Multiplier</Label>
                  <Input type="number" step="0.1" value={settings.bonus_subscriber_multiplier} onChange={(e) => setSettings({ ...settings, bonus_subscriber_multiplier: parseFloat(e.target.value) || 1 })} className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Follower Multiplier</Label>
                  <Input type="number" step="0.1" value={settings.bonus_follower_multiplier} onChange={(e) => setSettings({ ...settings, bonus_follower_multiplier: parseFloat(e.target.value) || 1 })} className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
              </div>

              <Button onClick={saveSettings} className="bg-emerald-500 hover:bg-emerald-600 text-black w-full">
                Save Settings
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
