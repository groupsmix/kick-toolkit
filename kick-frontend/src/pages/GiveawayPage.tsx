import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  Gift,
  Plus,
  Trophy,
  Users,
  Clock,
  Dices,
  RefreshCw,
  PartyPopper,
  Trash2,
  UserPlus,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { PageSkeleton } from "@/components/LoadingSkeleton";

interface GiveawayEntry {
  username: string;
  entered_at: string;
}

interface Giveaway {
  id: string;
  title: string;
  channel: string;
  keyword: string;
  status: string;
  duration_seconds: number;
  max_entries: number | null;
  subscriber_only: boolean;
  follower_only: boolean;
  entries: GiveawayEntry[];
  winner: string | null;
  created_at: string;
}

export function GiveawayPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [giveaways, setGiveaways] = useState<Giveaway[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [rolling, setRolling] = useState<string | null>(null);
  const [rollingName, setRollingName] = useState("");
  const [newGw, setNewGw] = useState({
    title: "",
    keyword: "!enter",
    duration_seconds: 300,
    max_entries: 0,
    subscriber_only: false,
    follower_only: false,
  });
  const [manualEntry, setManualEntry] = useState("");
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api<Giveaway[]>(`/api/giveaway?channel=${channel}`)
      .then(setGiveaways)
      .catch((err) => {
        setError(err.message || "Failed to load giveaways");
        toast.error("Failed to load giveaways");
      })
      .finally(() => setLoading(false));
  }, [channel]);

  const createGiveaway = async () => {
    if (!newGw.title) return;
    const gw = await api<Giveaway>("/api/giveaway/create", {
      method: "POST",
      body: JSON.stringify({
        ...newGw,
        channel,
        max_entries: newGw.max_entries || null,
        min_account_age_days: 0,
      }),
    });
    setGiveaways([gw, ...giveaways]);
    setShowCreate(false);
    setNewGw({ title: "", keyword: "!enter", duration_seconds: 300, max_entries: 0, subscriber_only: false, follower_only: false });
    toast.success(`Giveaway "${gw.title}" created`);
  };

  const addEntry = async (gwId: string) => {
    if (!manualEntry) return;
    try {
      await api(`/api/giveaway/${gwId}/enter`, {
        method: "POST",
        body: JSON.stringify({ username: manualEntry }),
      });
      const updated = await api<Giveaway>(`/api/giveaway/${gwId}`);
      setGiveaways(giveaways.map((g) => (g.id === gwId ? updated : g)));
      toast.success(`${manualEntry} entered`);
      setManualEntry("");
    } catch {
      toast.error("Failed to add entry");
    }
  };

  const rollWinner = async (gwId: string) => {
    setRolling(gwId);
    const gw = giveaways.find((g) => g.id === gwId);
    if (!gw) return;

    // Animate rolling through names
    const entries = gw.entries;
    let count = 0;
    const interval = setInterval(() => {
      const randomEntry = entries[Math.floor(Math.random() * entries.length)];
      setRollingName(randomEntry.username);
      count++;
      if (count > 20) {
        clearInterval(interval);
        // Actually roll from API
        api<{ winner: string; giveaway: Giveaway }>(`/api/giveaway/${gwId}/roll`, {
          method: "POST",
        }).then((result) => {
          setRollingName(result.winner);
          setTimeout(() => {
            setRolling(null);
            setRollingName("");
            setGiveaways(giveaways.map((g) => (g.id === gwId ? result.giveaway : g)));
          }, 2000);
        });
      }
    }, 100);
  };

  const reroll = async (gwId: string) => {
    await api<{ winner: string }>(`/api/giveaway/${gwId}/reroll`, {
      method: "POST",
    });
    const updated = await api<Giveaway>(`/api/giveaway/${gwId}`);
    setGiveaways(giveaways.map((g) => (g.id === gwId ? updated : g)));
  };

  const deleteGiveaway = async (gwId: string) => {
    try {
      await api(`/api/giveaway/${gwId}`, { method: "DELETE" });
      setGiveaways(giveaways.filter((g) => g.id !== gwId));
      toast.success("Giveaway deleted");
    } catch {
      toast.error("Failed to delete giveaway");
    }
  };

  const statusColor = (status: string) => {
    if (status === "active") return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    if (status === "completed") return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    return "bg-zinc-500/10 text-zinc-400 border-zinc-500/20";
  };

  if (loading) {
    return <PageSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-zinc-400">{error}</p>
        <Button onClick={() => window.location.reload()} variant="outline" className="border-zinc-700 text-zinc-300">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Giveaway Roller</h3>
          <p className="text-sm text-zinc-500">
            Create giveaways, collect entries via keyword, and roll winners
          </p>
        </div>
        <Button
          onClick={() => setShowCreate(!showCreate)}
          className="bg-emerald-500 hover:bg-emerald-600 text-black"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Giveaway
        </Button>
      </div>

      {/* Rolling Animation Overlay */}
      {rolling && (
        <Card className="bg-zinc-900 border-emerald-500/30 overflow-hidden">
          <CardContent className="p-8 text-center">
            <div className="mb-4">
              <Dices className="w-12 h-12 text-emerald-400 mx-auto animate-bounce" />
            </div>
            <p className="text-zinc-500 text-sm mb-2">Rolling winner...</p>
            <p className="text-4xl font-bold text-emerald-400 animate-pulse font-mono">
              {rollingName || "..."}
            </p>
            {rollingName && !giveaways.find((g) => g.id === rolling)?.winner && (
              <div className="mt-4 flex items-center justify-center gap-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-ping" />
                <span className="text-zinc-400 text-sm">Selecting...</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Create Form */}
      {showCreate && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Gift className="w-5 h-5 text-emerald-400" />
              Create New Giveaway
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-400 text-xs">Title</Label>
                <Input
                  value={newGw.title}
                  onChange={(e) => setNewGw({ ...newGw, title: e.target.value })}
                  placeholder="Steam Gift Card Giveaway"
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Entry Keyword</Label>
                <Input
                  value={newGw.keyword}
                  onChange={(e) => setNewGw({ ...newGw, keyword: e.target.value })}
                  placeholder="!enter"
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Duration (seconds)</Label>
                <Input
                  type="number"
                  value={newGw.duration_seconds}
                  onChange={(e) => setNewGw({ ...newGw, duration_seconds: parseInt(e.target.value) })}
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Max Entries (0 = unlimited)</Label>
                <Input
                  type="number"
                  value={newGw.max_entries}
                  onChange={(e) => setNewGw({ ...newGw, max_entries: parseInt(e.target.value) })}
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Switch
                  checked={newGw.subscriber_only}
                  onCheckedChange={(v) => setNewGw({ ...newGw, subscriber_only: v })}
                />
                <Label className="text-zinc-400 text-sm">Subscriber Only</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={newGw.follower_only}
                  onCheckedChange={(v) => setNewGw({ ...newGw, follower_only: v })}
                />
                <Label className="text-zinc-400 text-sm">Follower Only</Label>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setShowCreate(false)} className="text-zinc-400">
                Cancel
              </Button>
              <Button onClick={createGiveaway} className="bg-emerald-500 hover:bg-emerald-600 text-black">
                Create Giveaway
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Giveaway List */}
      <div className="space-y-4">
        {giveaways.map((gw) => (
          <Card key={gw.id} className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
            <CardContent className="p-0">
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-white font-semibold">{gw.title}</h4>
                      <Badge className={statusColor(gw.status)}>{gw.status}</Badge>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-xs text-zinc-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {gw.duration_seconds}s
                      </span>
                      <span className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {gw.entries.length} entries
                      </span>
                      <span>
                        Keyword: <code className="text-emerald-400">{gw.keyword}</code>
                      </span>
                      {gw.subscriber_only && <Badge variant="outline" className="text-[10px] border-purple-500/30 text-purple-400">Sub Only</Badge>}
                      {gw.follower_only && <Badge variant="outline" className="text-[10px] border-blue-500/30 text-blue-400">Follower Only</Badge>}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {gw.status === "active" && gw.entries.length > 0 && (
                      <Button
                        onClick={() => rollWinner(gw.id)}
                        className="bg-emerald-500 hover:bg-emerald-600 text-black"
                        disabled={rolling !== null}
                      >
                        <Dices className="w-4 h-4 mr-2" />
                        Roll Winner
                      </Button>
                    )}
                    {gw.status === "completed" && gw.winner && (
                      <Button
                        onClick={() => reroll(gw.id)}
                        variant="outline"
                        className="border-zinc-700 text-zinc-300"
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Reroll
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setConfirmDelete(gw.id)}
                      className="text-zinc-500 hover:text-red-400"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Winner Display */}
                {gw.winner && (
                  <div className="mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-3">
                    <PartyPopper className="w-6 h-6 text-emerald-400" />
                    <div>
                      <p className="text-xs text-zinc-500">Winner</p>
                      <p className="text-lg font-bold text-emerald-400">{gw.winner}</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Entries */}
              {gw.status === "active" && (
                <>
                  <Separator className="bg-zinc-800" />
                  <div className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Input
                        value={manualEntry}
                        onChange={(e) => setManualEntry(e.target.value)}
                        placeholder="Add entry manually..."
                        className="bg-zinc-800 border-zinc-700 text-white"
                        onKeyDown={(e) => e.key === "Enter" && addEntry(gw.id)}
                      />
                      <Button
                        onClick={() => addEntry(gw.id)}
                        variant="outline"
                        className="border-zinc-700 text-zinc-300"
                      >
                        <UserPlus className="w-4 h-4 mr-2" />
                        Add
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {gw.entries.map((entry) => (
                        <Badge
                          key={entry.username}
                          variant="outline"
                          className="border-zinc-700 text-zinc-300"
                        >
                          {entry.username}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {gw.status === "completed" && gw.entries.length > 0 && (
                <>
                  <Separator className="bg-zinc-800" />
                  <div className="p-4">
                    <p className="text-xs text-zinc-500 mb-2">All Entries ({gw.entries.length})</p>
                    <div className="flex flex-wrap gap-2">
                      {gw.entries.map((entry) => (
                        <Badge
                          key={entry.username}
                          variant="outline"
                          className={`${entry.username === gw.winner ? "border-emerald-500/30 text-emerald-400" : "border-zinc-700 text-zinc-400"}`}
                        >
                          {entry.username === gw.winner && <Trophy className="w-3 h-3 mr-1" />}
                          {entry.username}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      <ConfirmDialog
        open={confirmDelete !== null}
        onOpenChange={(open) => { if (!open) setConfirmDelete(null); }}
        title="Delete Giveaway"
        description="Are you sure you want to delete this giveaway? This action cannot be undone and all entries will be lost."
        confirmLabel="Delete"
        variant="danger"
        onConfirm={() => { if (confirmDelete) deleteGiveaway(confirmDelete); }}
      />
    </div>
  );
}
