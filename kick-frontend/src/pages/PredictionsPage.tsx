import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { TrendingUp, Plus, Lock, CheckCircle, XCircle } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface Prediction {
  id: string;
  channel: string;
  title: string;
  outcomes: string[];
  outcome_pools: Record<string, number>;
  status: string;
  winning_outcome: string | null;
  created_at: string;
}

export function PredictionsPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [title, setTitle] = useState("");
  const [outcomes, setOutcomes] = useState(["", ""]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<Prediction[]>(`/api/predictions/${channel}`)
      .then(setPredictions)
      .catch(() => toast.error("Failed to load predictions"))
      .finally(() => setLoading(false));
  }, [channel]);

  const createPrediction = async () => {
    const valid = outcomes.filter((o) => o.trim());
    if (!title.trim() || valid.length < 2) {
      toast.error("Need a title and at least 2 outcomes");
      return;
    }
    try {
      const result = await api<Prediction>(`/api/predictions/${channel}`, {
        method: "POST",
        body: JSON.stringify({ title, outcomes: valid }),
      });
      setPredictions([result, ...predictions]);
      setTitle("");
      setOutcomes(["", ""]);
      setShowAdd(false);
      toast.success("Prediction created");
    } catch {
      toast.error("Failed to create prediction");
    }
  };

  const lockPrediction = async (id: string) => {
    try {
      const result = await api<Prediction>(`/api/predictions/${channel}/${id}/lock`, { method: "POST" });
      setPredictions(predictions.map((p) => (p.id === id ? result : p)));
      toast.success("Prediction locked");
    } catch {
      toast.error("Failed to lock");
    }
  };

  const resolvePrediction = async (id: string, outcome: string) => {
    try {
      const result = await api<Prediction>(`/api/predictions/${channel}/${id}/resolve`, {
        method: "POST",
        body: JSON.stringify({ winning_outcome: outcome }),
      });
      setPredictions(predictions.map((p) => (p.id === id ? result : p)));
      toast.success("Prediction resolved");
    } catch {
      toast.error("Failed to resolve");
    }
  };

  const cancelPrediction = async (id: string) => {
    try {
      const result = await api<Prediction>(`/api/predictions/${channel}/${id}/cancel`, { method: "POST" });
      setPredictions(predictions.map((p) => (p.id === id ? result : p)));
      toast.success("Prediction cancelled");
    } catch {
      toast.error("Failed to cancel");
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
            <TrendingUp className="w-6 h-6 text-amber-400" />
            Predictions
          </h2>
          <p className="text-sm text-zinc-500">Let viewers bet points on outcomes</p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
          <Plus className="w-4 h-4 mr-2" />
          New Prediction
        </Button>
      </div>

      {showAdd && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardContent className="p-4 space-y-3">
            <div>
              <Label className="text-zinc-400 text-xs">Title</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Will I win this match?" className="bg-zinc-800 border-zinc-700 text-white" />
            </div>
            <div className="space-y-2">
              <Label className="text-zinc-400 text-xs">Outcomes</Label>
              {outcomes.map((o, i) => (
                <Input key={i} value={o} onChange={(e) => { const oc = [...outcomes]; oc[i] = e.target.value; setOutcomes(oc); }} placeholder={`Outcome ${i + 1}`} className="bg-zinc-800 border-zinc-700 text-white" />
              ))}
              <Button variant="ghost" size="sm" onClick={() => setOutcomes([...outcomes, ""])} className="text-zinc-400 text-xs">
                <Plus className="w-3 h-3 mr-1" /> Add outcome
              </Button>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" onClick={() => setShowAdd(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={createPrediction} className="bg-emerald-500 hover:bg-emerald-600 text-black">Create</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {predictions.map((pred) => {
          const totalPool = Object.values(pred.outcome_pools || {}).reduce((a, b) => a + b, 0);
          return (
            <Card key={pred.id} className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-white font-medium">{pred.title}</h3>
                    <Badge variant="outline" className={`text-[10px] mt-1 ${
                      pred.status === "open" ? "border-emerald-500/30 text-emerald-400" :
                      pred.status === "locked" ? "border-amber-500/30 text-amber-400" :
                      "border-zinc-700 text-zinc-500"
                    }`}>
                      {pred.status} &middot; {totalPool} pts pooled
                    </Badge>
                  </div>
                  <div className="flex gap-1">
                    {pred.status === "open" && (
                      <Button variant="ghost" size="sm" className="text-amber-400 text-xs" onClick={() => lockPrediction(pred.id)}>
                        <Lock className="w-3 h-3 mr-1" /> Lock
                      </Button>
                    )}
                    {pred.status === "locked" && (
                      <Button variant="ghost" size="sm" className="text-red-400 text-xs" onClick={() => cancelPrediction(pred.id)}>
                        <XCircle className="w-3 h-3 mr-1" /> Cancel
                      </Button>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {(pred.outcomes || []).map((outcome) => {
                    const pool = pred.outcome_pools?.[outcome] || 0;
                    const isWinner = pred.winning_outcome === outcome;
                    return (
                      <div
                        key={outcome}
                        className={`p-3 rounded-lg border ${isWinner ? "border-emerald-500/30 bg-emerald-500/5" : "border-zinc-800 bg-zinc-900/50"}`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-white">{outcome}</span>
                          {isWinner && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                        </div>
                        <span className="text-xs text-zinc-500">{pool} pts</span>
                        {pred.status === "locked" && (
                          <Button variant="ghost" size="sm" className="mt-1 text-[10px] text-emerald-400 p-0 h-auto" onClick={() => resolvePrediction(pred.id, outcome)}>
                            Select winner
                          </Button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          );
        })}
        {predictions.length === 0 && <p className="text-center text-zinc-600 py-8">No predictions yet.</p>}
      </div>
    </div>
  );
}
