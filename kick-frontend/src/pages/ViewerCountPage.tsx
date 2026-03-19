import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { Users, TrendingUp, TrendingDown, BarChart3 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface ViewerSnapshot {
  id: string;
  viewer_count: number;
  recorded_at: string;
}

interface ViewerStats {
  peak: number;
  average: number;
  min: number;
  total_snapshots: number;
}

export function ViewerCountPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [history, setHistory] = useState<ViewerSnapshot[]>([]);
  const [stats, setStats] = useState<ViewerStats>({ peak: 0, average: 0, min: 0, total_snapshots: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<ViewerSnapshot[]>(`/api/viewer-count/${channel}/history`),
      api<ViewerStats>(`/api/viewer-count/${channel}/stats`),
    ])
      .then(([h, s]) => { setHistory(h); setStats(s); })
      .catch(() => toast.error("Failed to load viewer data"))
      .finally(() => setLoading(false));
  }, [channel]);

  const recordSnapshot = async () => {
    try {
      const count = Math.floor(Math.random() * 500) + 50;
      const result = await api<ViewerSnapshot>(`/api/viewer-count/${channel}/snapshot?viewer_count=${count}`, { method: "POST" });
      setHistory([result, ...history]);
      toast.success(`Recorded ${count} viewers`);
    } catch {
      toast.error("Failed to record");
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
            <Users className="w-6 h-6 text-blue-400" />
            Viewer Count Tracker
          </h2>
          <p className="text-sm text-zinc-500">Track viewer count over time</p>
        </div>
        <Button onClick={recordSnapshot} className="bg-emerald-500 hover:bg-emerald-600 text-black">
          Record Snapshot
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4 flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-emerald-400" />
            <div>
              <p className="text-2xl font-bold text-white">{stats.peak}</p>
              <p className="text-xs text-zinc-500">Peak Viewers</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4 flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-blue-400" />
            <div>
              <p className="text-2xl font-bold text-white">{stats.average}</p>
              <p className="text-xs text-zinc-500">Average Viewers</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4 flex items-center gap-3">
            <TrendingDown className="w-8 h-8 text-red-400" />
            <div>
              <p className="text-2xl font-bold text-white">{stats.min}</p>
              <p className="text-xs text-zinc-500">Min Viewers</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-white">History ({history.length} snapshots)</CardTitle>
        </CardHeader>
        <CardContent>
          {history.length > 0 ? (
            <div className="h-48 flex items-end gap-1">
              {history.slice(0, 60).reverse().map((snap) => {
                const maxCount = stats.peak || 1;
                const height = Math.max(4, (snap.viewer_count / maxCount) * 100);
                return (
                  <div
                    key={snap.id}
                    className="flex-1 bg-emerald-500/60 rounded-t hover:bg-emerald-400/80 transition-colors"
                    style={{ height: `${height}%` }}
                    title={`${snap.viewer_count} viewers at ${new Date(snap.recorded_at).toLocaleTimeString()}`}
                  />
                );
              })}
            </div>
          ) : (
            <p className="text-center text-zinc-600 py-8">No viewer data yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
