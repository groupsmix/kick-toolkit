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
  Music,
  Play,
  SkipForward,
  Trash2,
  Plus,
  ListMusic,
  Settings,
  History,
  X,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface SongEntry {
  id: string;
  channel: string;
  username: string;
  title: string;
  artist: string;
  url: string | null;
  platform: string;
  duration_seconds: number;
  status: string;
  position: number;
  created_at: string;
}

interface QueueSettings {
  channel: string;
  enabled: boolean;
  max_queue_size: number;
  max_duration_seconds: number;
  allow_duplicates: boolean;
  subscriber_only: boolean;
  cost_per_request: number;
}

export function SongRequestPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [queue, setQueue] = useState<SongEntry[]>([]);
  const [history, setHistory] = useState<SongEntry[]>([]);
  const [settings, setSettings] = useState<QueueSettings>({
    channel: "",
    enabled: true,
    max_queue_size: 50,
    max_duration_seconds: 600,
    allow_duplicates: false,
    subscriber_only: false,
    cost_per_request: 0,
  });
  const [showAdd, setShowAdd] = useState(false);
  const [newSong, setNewSong] = useState({ username: "", title: "", artist: "", url: "", platform: "youtube" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<SongEntry[]>(`/api/songs/queue/${channel}`).then(setQueue),
      api<SongEntry[]>(`/api/songs/history/${channel}`).then(setHistory),
      api<QueueSettings>(`/api/songs/settings/${channel}`).then(setSettings),
    ])
      .catch(() => toast.error("Failed to load song request data"))
      .finally(() => setLoading(false));
  }, [channel]);

  const addSong = async () => {
    if (!newSong.title) return;
    try {
      const result = await api<SongEntry>(`/api/songs/queue/${channel}`, {
        method: "POST",
        body: JSON.stringify({ ...newSong, duration_seconds: 0 }),
      });
      setQueue([...queue, result]);
      setNewSong({ username: "", title: "", artist: "", url: "", platform: "youtube" });
      setShowAdd(false);
      toast.success(`"${result.title}" added to queue`);
    } catch {
      toast.error("Failed to add song");
    }
  };

  const playSong = async (id: string) => {
    try {
      const result = await api<SongEntry>(`/api/songs/queue/${channel}/${id}/play`, { method: "POST" });
      setQueue(queue.map((s) => s.id === id ? result : (s.status === "playing" ? { ...s, status: "played" } : s)));
      toast.success("Now playing");
    } catch {
      toast.error("Failed to play song");
    }
  };

  const skipSong = async (id: string) => {
    try {
      await api(`/api/songs/queue/${channel}/${id}/skip`, { method: "POST" });
      setQueue(queue.filter((s) => s.id !== id));
      toast.success("Song skipped");
    } catch {
      toast.error("Failed to skip song");
    }
  };

  const removeSong = async (id: string) => {
    try {
      await api(`/api/songs/queue/${channel}/${id}`, { method: "DELETE" });
      setQueue(queue.filter((s) => s.id !== id));
      toast.success("Song removed");
    } catch {
      toast.error("Failed to remove song");
    }
  };

  const clearQueue = async () => {
    try {
      await api(`/api/songs/queue/${channel}`, { method: "DELETE" });
      setQueue(queue.filter((s) => s.status === "playing"));
      toast.success("Queue cleared");
    } catch {
      toast.error("Failed to clear queue");
    }
  };

  const saveSettings = async () => {
    try {
      const result = await api<QueueSettings>(`/api/songs/settings/${channel}`, {
        method: "POST",
        body: JSON.stringify(settings),
      });
      setSettings(result);
      toast.success("Settings saved");
    } catch {
      toast.error("Failed to save settings");
    }
  };

  const nowPlaying = queue.find((s) => s.status === "playing");
  const queued = queue.filter((s) => s.status === "queued");

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
            <Music className="w-6 h-6 text-purple-400" />
            Song Requests
          </h2>
          <p className="text-sm text-zinc-500">Manage song request queue from viewers</p>
        </div>
        <Badge className={settings.enabled ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-700/50 text-zinc-400"}>
          {settings.enabled ? "Active" : "Disabled"}
        </Badge>
      </div>

      {nowPlaying && (
        <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/20">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-full bg-purple-500/20">
              <Play className="w-5 h-5 text-purple-400" />
            </div>
            <div className="flex-1">
              <p className="text-xs text-purple-400 uppercase tracking-wider font-semibold">Now Playing</p>
              <p className="text-lg text-white font-bold">{nowPlaying.title}</p>
              {nowPlaying.artist && <p className="text-sm text-zinc-400">{nowPlaying.artist}</p>}
              <p className="text-xs text-zinc-500">Requested by {nowPlaying.username}</p>
            </div>
            <Button variant="ghost" size="icon" onClick={() => skipSong(nowPlaying.id)} className="text-zinc-400 hover:text-white">
              <SkipForward className="w-5 h-5" />
            </Button>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="queue" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="queue" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <ListMusic className="w-4 h-4 mr-2" />
            Queue ({queued.length})
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <History className="w-4 h-4 mr-2" />
            History
          </TabsTrigger>
          <TabsTrigger value="settings" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="queue" className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Song Queue</h3>
            <div className="flex gap-2">
              {queued.length > 0 && (
                <Button variant="outline" onClick={clearQueue} className="border-zinc-700 text-zinc-400 hover:text-red-400">
                  <X className="w-4 h-4 mr-2" />
                  Clear
                </Button>
              )}
              <Button onClick={() => setShowAdd(!showAdd)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
                <Plus className="w-4 h-4 mr-2" />
                Add Song
              </Button>
            </div>
          </div>

          {showAdd && (
            <Card className="bg-zinc-900/50 border-emerald-500/20">
              <CardContent className="p-4 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-zinc-400 text-xs">Song Title</Label>
                    <Input value={newSong.title} onChange={(e) => setNewSong({ ...newSong, title: e.target.value })} placeholder="Song name" className="bg-zinc-800 border-zinc-700 text-white" />
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">Artist</Label>
                    <Input value={newSong.artist} onChange={(e) => setNewSong({ ...newSong, artist: e.target.value })} placeholder="Artist name" className="bg-zinc-800 border-zinc-700 text-white" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-zinc-400 text-xs">Requested By</Label>
                    <Input value={newSong.username} onChange={(e) => setNewSong({ ...newSong, username: e.target.value })} placeholder="Username" className="bg-zinc-800 border-zinc-700 text-white" />
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">URL (optional)</Label>
                    <Input value={newSong.url} onChange={(e) => setNewSong({ ...newSong, url: e.target.value })} placeholder="https://youtube.com/..." className="bg-zinc-800 border-zinc-700 text-white" />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" onClick={() => setShowAdd(false)} className="text-zinc-400">Cancel</Button>
                  <Button onClick={addSong} className="bg-emerald-500 hover:bg-emerald-600 text-black">Add to Queue</Button>
                </div>
              </CardContent>
            </Card>
          )}

          {queued.length === 0 && !showAdd ? (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Music className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">Queue is empty. Songs requested via chat will appear here.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {queued.map((song, index) => (
                <Card key={song.id} className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
                  <CardContent className="p-4 flex items-center gap-4">
                    <span className="text-zinc-600 font-mono text-sm w-6 text-center">{index + 1}</span>
                    <div className="flex-1">
                      <span className="text-white font-medium">{song.title}</span>
                      {song.artist && <span className="text-zinc-500 ml-2">- {song.artist}</span>}
                      <p className="text-xs text-zinc-500 mt-1">Requested by {song.username}</p>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon" className="text-zinc-500 hover:text-emerald-400" onClick={() => playSong(song.id)} title="Play">
                        <Play className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="text-zinc-500 hover:text-amber-400" onClick={() => skipSong(song.id)} title="Skip">
                        <SkipForward className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="text-zinc-500 hover:text-red-400" onClick={() => removeSong(song.id)} title="Remove">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-4 mt-4">
          <h3 className="text-lg font-semibold text-white">Recently Played</h3>
          {history.length === 0 ? (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <History className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">No song history yet.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {history.map((song) => (
                <Card key={song.id} className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-3 flex items-center gap-3">
                    <div className="flex-1">
                      <span className="text-zinc-300 text-sm">{song.title}</span>
                      {song.artist && <span className="text-zinc-600 ml-2 text-sm">- {song.artist}</span>}
                    </div>
                    <Badge variant="outline" className={`text-[10px] ${song.status === "played" ? "border-emerald-500/30 text-emerald-400" : "border-zinc-700 text-zinc-500"}`}>
                      {song.status}
                    </Badge>
                    <span className="text-xs text-zinc-600">{song.username}</span>
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
                Queue Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-white">Enable Song Requests</Label>
                  <p className="text-xs text-zinc-500">Allow viewers to request songs via chat</p>
                </div>
                <Switch checked={settings.enabled} onCheckedChange={(v) => setSettings({ ...settings, enabled: v })} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-white">Subscriber Only</Label>
                  <p className="text-xs text-zinc-500">Only subscribers can request songs</p>
                </div>
                <Switch checked={settings.subscriber_only} onCheckedChange={(v) => setSettings({ ...settings, subscriber_only: v })} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-white">Allow Duplicates</Label>
                  <p className="text-xs text-zinc-500">Allow the same song to be requested multiple times</p>
                </div>
                <Switch checked={settings.allow_duplicates} onCheckedChange={(v) => setSettings({ ...settings, allow_duplicates: v })} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-zinc-400 text-xs">Max Queue Size</Label>
                  <Input type="number" value={settings.max_queue_size} onChange={(e) => setSettings({ ...settings, max_queue_size: parseInt(e.target.value) || 50 })} className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Max Song Duration (seconds)</Label>
                  <Input type="number" value={settings.max_duration_seconds} onChange={(e) => setSettings({ ...settings, max_duration_seconds: parseInt(e.target.value) || 600 })} className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Points Cost Per Request</Label>
                <Input type="number" value={settings.cost_per_request} onChange={(e) => setSettings({ ...settings, cost_per_request: parseInt(e.target.value) || 0 })} className="bg-zinc-800 border-zinc-700 text-white" />
                <p className="text-xs text-zinc-600 mt-1">Set to 0 for free requests</p>
              </div>
              <Button onClick={saveSettings} className="bg-emerald-500 hover:bg-emerald-600 text-black w-full">Save Settings</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
