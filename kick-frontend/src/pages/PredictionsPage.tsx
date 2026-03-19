import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  TrendingUp,
  Plus,
  Lock,
  CheckCircle,
  XCircle,
  Clock,
  Coins,
  Trophy,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface OutcomeDetail {
  index: number;
  title: string;
  bet_count: number;
  total_amount: number;
}

interface Prediction {
  id: string;
  channel: string;
  title: string;
  outcomes: string[];
  lock_seconds: number;
  status: string;
  winning_index: number | null;
  created_at: string;
  locked_at: string | null;
  resolved_at: string | null;
  total_bettors?: number;
  total_pool?: number;
  outcome_details?: OutcomeDetail[];
}

export function PredictionsPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newOutcomes, setNewOutcomes] = useState(["", ""]);
  const [newLockSeconds, setNewLockSeconds] = useState(300);

  const fetchPredictions = async () => {
    try {
      const data = await api<Prediction[]>(`/api/predictions/${channel}`);
      const withDetails = await Promise.all(
        data.map(async (pred) => {
          try {
            const detail = await api<Prediction>(`/api/predictions/${channel}/${pred.id}`);
            return { ...pred, ...detail };
          } catch {
            return pred;
          }
        })
      );
      setPredictions(withDetails);
    } catch {
      toast.error("Failed to load predictions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, [channel]);

  const createPrediction = async () => {
    const validOutcomes = newOutcomes.filter((o) => o.trim());
    if (!newTitle.trim() || validOutcomes.length < 2) {
      toast.error("Title and at least 2 outcomes are required");
      return;
    }
    try {
      await api(`/api/predictions/${channel}`, {
        method: "POST",
        body: JSON.stringify({
          title: newTitle,
          outcomes: validOutcomes,
          lock_seconds: newLockSeconds,
        }),
      });
      toast.success("Prediction created");
      setShowCreate(false);
      setNewTitle("");
      setNewOutcomes(["", ""]);
      fetchPredictions();
    } catch {
      toast.error("Failed to create prediction");
    }
  };

  const lockPrediction = async (predId: string) => {
    try {
      await api(`/api/predictions/${channel}/${predId}/lock`, { method: "POST" });
      toast.success("Prediction locked - no more bets");
      fetchPredictions();
    } catch {
      toast.error("Failed to lock prediction");
    }
  };

  const resolvePrediction = async (predId: string, winningIndex: number) => {
    try {
      await api(`/api/predictions/${channel}/${predId}/resolve`, {
        method: "POST",
        body: JSON.stringify({ winning_index: winningIndex }),
      });
      toast.success("Prediction resolved! Winnings distributed.");
      fetchPredictions();
    } catch {
      toast.error("Failed to resolve prediction");
    }
  };

  const cancelPrediction = async (predId: string) => {
    try {
      await api(`/api/predictions/${channel}/${predId}/cancel`, { method: "POST" });
      toast.success("Prediction cancelled. All bets refunded.");
      fetchPredictions();
    } catch {
      toast.error("Failed to cancel prediction");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const openPreds = predictions.filter((p) => p.status === "open" || p.status === "locked");
  const closedPreds = predictions.filter((p) => p.status === "resolved" || p.status === "cancelled");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-purple-400" />
            Predictions
          </h2>
          <p className="text-sm text-zinc-500">Let viewers bet points on outcomes</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
          <Plus className="w-4 h-4 mr-2" />
          New Prediction
        </Button>
      </div>

      {showCreate && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardHeader>
            <CardTitle className="text-white text-lg">Create New Prediction</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-zinc-400 text-xs">Prediction Question</Label>
              <Input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Will we win the next match?"
                className="bg-zinc-800 border-zinc-700 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-zinc-400 text-xs">Outcomes</Label>
              {newOutcomes.map((outcome, i) => (
                <div key={i} className="flex gap-2">
                  <Input
                    value={outcome}
                    onChange={(e) => {
                      const updated = [...newOutcomes];
                      updated[i] = e.target.value;
                      setNewOutcomes(updated);
                    }}
                    placeholder={`Outcome ${i + 1}`}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                  {newOutcomes.length > 2 && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-zinc-500 hover:text-red-400"
                      onClick={() => setNewOutcomes(newOutcomes.filter((_, idx) => idx !== i))}
                    >
                      <XCircle className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              {newOutcomes.length < 10 && (
                <Button
                  variant="ghost"
                  className="text-zinc-400 text-sm"
                  onClick={() => setNewOutcomes([...newOutcomes, ""])}
                >
                  <Plus className="w-4 h-4 mr-1" /> Add Outcome
                </Button>
              )}
            </div>
            <div>
              <Label className="text-zinc-400 text-xs">Lock Timer (seconds)</Label>
              <Input
                type="number"
                value={newLockSeconds}
                onChange={(e) => setNewLockSeconds(parseInt(e.target.value) || 300)}
                className="bg-zinc-800 border-zinc-700 text-white"
              />
              <p className="text-xs text-zinc-600 mt-1">Betting window closes after this duration</p>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setShowCreate(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={createPrediction} className="bg-emerald-500 hover:bg-emerald-600 text-black">Create Prediction</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="active" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="active" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Clock className="w-4 h-4 mr-2" />
            Active ({openPreds.length})
          </TabsTrigger>
          <TabsTrigger value="closed" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <CheckCircle className="w-4 h-4 mr-2" />
            Resolved ({closedPreds.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4 mt-4">
          {openPreds.length === 0 ? (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <TrendingUp className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">No active predictions. Create one to engage viewers!</p>
              </CardContent>
            </Card>
          ) : (
            openPreds.map((pred) => (
              <PredictionCard
                key={pred.id}
                prediction={pred}
                onLock={() => lockPrediction(pred.id)}
                onResolve={(idx) => resolvePrediction(pred.id, idx)}
                onCancel={() => cancelPrediction(pred.id)}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="closed" className="space-y-4 mt-4">
          {closedPreds.length === 0 ? (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Trophy className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">No resolved predictions yet.</p>
              </CardContent>
            </Card>
          ) : (
            closedPreds.map((pred) => (
              <PredictionCard key={pred.id} prediction={pred} />
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function PredictionCard({
  prediction,
  onLock,
  onResolve,
  onCancel,
}: {
  prediction: Prediction;
  onLock?: () => void;
  onResolve?: (idx: number) => void;
  onCancel?: () => void;
}) {
  const details = prediction.outcome_details || [];
  const totalPool = prediction.total_pool || 0;

  const statusColor: Record<string, string> = {
    open: "bg-emerald-500/20 text-emerald-400",
    locked: "bg-amber-500/20 text-amber-400",
    resolved: "bg-blue-500/20 text-blue-400",
    cancelled: "bg-zinc-700/50 text-zinc-400",
  };

  return (
    <Card className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-white font-semibold text-lg">{prediction.title}</h3>
            <div className="flex items-center gap-2 mt-1">
              <Badge className={statusColor[prediction.status] || "bg-zinc-700/50 text-zinc-400"}>
                {prediction.status === "locked" && <Lock className="w-3 h-3 mr-1" />}
                {prediction.status}
              </Badge>
              <span className="text-xs text-zinc-500 flex items-center gap-1">
                <Coins className="w-3 h-3" /> {totalPool.toLocaleString()} in pool
              </span>
              <span className="text-xs text-zinc-500">{prediction.total_bettors || 0} bettors</span>
            </div>
          </div>
          <div className="flex gap-2">
            {prediction.status === "open" && onLock && (
              <Button onClick={onLock} variant="outline" size="sm" className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10">
                <Lock className="w-3 h-3 mr-1" /> Lock
              </Button>
            )}
            {(prediction.status === "open" || prediction.status === "locked") && onCancel && (
              <Button onClick={onCancel} variant="outline" size="sm" className="border-zinc-700 text-zinc-400 hover:bg-zinc-800">
                Cancel
              </Button>
            )}
          </div>
        </div>
        <div className="space-y-3">
          {details.length > 0
            ? details.map((d) => {
                const pct = totalPool > 0 ? (d.total_amount / totalPool) * 100 : 0;
                const isWinner = prediction.winning_index === d.index;
                return (
                  <div key={d.index} className={isWinner ? "ring-1 ring-emerald-500/50 rounded-lg p-2" : "p-2"}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className={isWinner ? "text-emerald-400 font-medium" : "text-zinc-300"}>
                        {isWinner && <Trophy className="w-3 h-3 inline mr-1" />}
                        {d.title}
                      </span>
                      <span className="text-zinc-400">{d.bet_count} bets - {d.total_amount.toLocaleString()} pts ({pct.toFixed(1)}%)</span>
                    </div>
                    <div className="w-full bg-zinc-800 rounded-full h-2.5">
                      <div
                        className={`h-2.5 rounded-full transition-all duration-500 ${isWinner ? "bg-emerald-500" : "bg-purple-500"}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    {(prediction.status === "open" || prediction.status === "locked") && onResolve && (
                      <Button
                        onClick={() => onResolve(d.index)}
                        variant="ghost"
                        size="sm"
                        className="text-xs text-zinc-500 hover:text-emerald-400 mt-1"
                      >
                        <CheckCircle className="w-3 h-3 mr-1" /> Resolve as winner
                      </Button>
                    )}
                  </div>
                );
              })
            : (prediction.outcomes || []).map((outcome, i) => (
                <div key={i} className="p-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-zinc-300">{outcome}</span>
                    <span className="text-zinc-400">0 bets</span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-2.5" />
                </div>
              ))}
        </div>
      </CardContent>
    </Card>
  );
}
