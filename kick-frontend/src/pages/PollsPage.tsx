import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { BarChart3, Plus, Trash2, CheckCircle } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface Poll {
  id: string;
  channel: string;
  question: string;
  options: string[];
  votes: Record<string, number>;
  status: string;
  created_at: string;
}

export function PollsPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [polls, setPolls] = useState<Poll[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [question, setQuestion] = useState("");
  const [options, setOptions] = useState(["", ""]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<Poll[]>(`/api/polls/${channel}`)
      .then(setPolls)
      .catch(() => toast.error("Failed to load polls"))
      .finally(() => setLoading(false));
  }, [channel]);

  const createPoll = async () => {
    const validOptions = options.filter((o) => o.trim());
    if (!question.trim() || validOptions.length < 2) {
      toast.error("Need a question and at least 2 options");
      return;
    }
    try {
      const result = await api<Poll>(`/api/polls/${channel}`, {
        method: "POST",
        body: JSON.stringify({ question, options: validOptions }),
      });
      setPolls([result, ...polls]);
      setQuestion("");
      setOptions(["", ""]);
      setShowAdd(false);
      toast.success("Poll created");
    } catch {
      toast.error("Failed to create poll");
    }
  };

  const closePoll = async (pollId: string) => {
    try {
      const result = await api<Poll>(`/api/polls/${channel}/${pollId}/close`, { method: "POST" });
      setPolls(polls.map((p) => (p.id === pollId ? result : p)));
      toast.success("Poll closed");
    } catch {
      toast.error("Failed to close poll");
    }
  };

  const deletePoll = async (pollId: string) => {
    try {
      await api(`/api/polls/${channel}/${pollId}`, { method: "DELETE" });
      setPolls(polls.filter((p) => p.id !== pollId));
      toast.success("Poll deleted");
    } catch {
      toast.error("Failed to delete poll");
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
            <BarChart3 className="w-6 h-6 text-purple-400" />
            Chat Polls
          </h2>
          <p className="text-sm text-zinc-500">Create polls for your viewers to vote on</p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
          <Plus className="w-4 h-4 mr-2" />
          New Poll
        </Button>
      </div>

      {showAdd && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardContent className="p-4 space-y-3">
            <div>
              <Label className="text-zinc-400 text-xs">Question</Label>
              <Input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="What game should I play next?" className="bg-zinc-800 border-zinc-700 text-white" />
            </div>
            <div className="space-y-2">
              <Label className="text-zinc-400 text-xs">Options</Label>
              {options.map((opt, i) => (
                <Input key={i} value={opt} onChange={(e) => { const o = [...options]; o[i] = e.target.value; setOptions(o); }} placeholder={`Option ${i + 1}`} className="bg-zinc-800 border-zinc-700 text-white" />
              ))}
              <Button variant="ghost" size="sm" onClick={() => setOptions([...options, ""])} className="text-zinc-400 text-xs">
                <Plus className="w-3 h-3 mr-1" /> Add option
              </Button>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" onClick={() => setShowAdd(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={createPoll} className="bg-emerald-500 hover:bg-emerald-600 text-black">Create Poll</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {polls.map((poll) => {
          const totalVotes = Object.values(poll.votes || {}).reduce((a, b) => a + b, 0);
          return (
            <Card key={poll.id} className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-white font-medium">{poll.question}</h3>
                    <Badge variant="outline" className={`text-[10px] mt-1 ${poll.status === "open" ? "border-emerald-500/30 text-emerald-400" : "border-zinc-700 text-zinc-500"}`}>
                      {poll.status} &middot; {totalVotes} vote{totalVotes !== 1 ? "s" : ""}
                    </Badge>
                  </div>
                  <div className="flex gap-1">
                    {poll.status === "open" && (
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-400 hover:text-emerald-400" onClick={() => closePoll(poll.id)}>
                        <CheckCircle className="w-4 h-4" />
                      </Button>
                    )}
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-600 hover:text-red-400" onClick={() => deletePoll(poll.id)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  {(poll.options || []).map((opt) => {
                    const count = poll.votes?.[opt] || 0;
                    const pct = totalVotes > 0 ? (count / totalVotes) * 100 : 0;
                    return (
                      <div key={opt}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-zinc-300">{opt}</span>
                          <span className="text-zinc-500">{count} ({pct.toFixed(0)}%)</span>
                        </div>
                        <Progress value={pct} className="h-2" />
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          );
        })}
        {polls.length === 0 && <p className="text-center text-zinc-600 py-8">No polls yet. Create one to get started.</p>}
      </div>
    </div>
  );
}
