import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { Crosshair, Plus, Minus, RotateCcw } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface KDCounter {
  id: string;
  channel: string;
  kills: number;
  deaths: number;
  assists: number;
  game: string;
}

export function KDCounterPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [counter, setCounter] = useState<KDCounter | null>(null);
  const [game, setGame] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<KDCounter>(`/api/kd-counter/${channel}`)
      .then((c) => { if (c.id) setCounter(c); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [channel]);

  const createCounter = async () => {
    try {
      const result = await api<KDCounter>(`/api/kd-counter/${channel}?game=${encodeURIComponent(game)}`, { method: "POST" });
      setCounter(result);
      toast.success("Counter created");
    } catch {
      toast.error("Failed to create counter");
    }
  };

  const increment = async (field: string, amount: number) => {
    if (!counter) return;
    try {
      const result = await api<KDCounter>(`/api/kd-counter/${channel}/${counter.id}/increment?field=${field}&amount=${amount}`, { method: "POST" });
      setCounter(result);
    } catch {
      toast.error("Failed to update");
    }
  };

  const reset = async () => {
    if (!counter) return;
    try {
      const result = await api<KDCounter>(`/api/kd-counter/${channel}/${counter.id}/reset`, { method: "POST" });
      setCounter(result);
      toast.success("Counter reset");
    } catch {
      toast.error("Failed to reset");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const kd = counter && counter.deaths > 0 ? (counter.kills / counter.deaths).toFixed(2) : counter ? counter.kills.toFixed(2) : "0.00";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Crosshair className="w-6 h-6 text-red-400" />
          Kill / Death Counter
        </h2>
        <p className="text-sm text-zinc-500">Track your K/D/A in real-time</p>
      </div>

      {!counter ? (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-6 text-center space-y-4">
            <p className="text-zinc-400">No active counter. Create one to start tracking.</p>
            <div className="flex items-center gap-3 justify-center">
              <Input value={game} onChange={(e) => setGame(e.target.value)} placeholder="Game name" className="bg-zinc-800 border-zinc-700 text-white w-48" />
              <Button onClick={createCounter} className="bg-emerald-500 hover:bg-emerald-600 text-black">Create Counter</Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Kills", value: counter.kills, field: "kills", color: "text-emerald-400" },
              { label: "Deaths", value: counter.deaths, field: "deaths", color: "text-red-400" },
              { label: "Assists", value: counter.assists, field: "assists", color: "text-blue-400" },
              { label: "K/D Ratio", value: kd, field: null, color: "text-amber-400" },
            ].map((stat) => (
              <Card key={stat.label} className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4 text-center">
                  <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
                  <p className="text-xs text-zinc-500 mt-1">{stat.label}</p>
                  {stat.field && (
                    <div className="flex gap-2 justify-center mt-3">
                      <Button size="icon" variant="outline" className="h-8 w-8 border-zinc-700" onClick={() => increment(stat.field!, 1)}>
                        <Plus className="w-3 h-3" />
                      </Button>
                      <Button size="icon" variant="outline" className="h-8 w-8 border-zinc-700" onClick={() => increment(stat.field!, -1)}>
                        <Minus className="w-3 h-3" />
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="flex justify-center">
            <Button variant="outline" onClick={reset} className="border-zinc-700 text-zinc-400">
              <RotateCcw className="w-4 h-4 mr-2" /> Reset Counter
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
