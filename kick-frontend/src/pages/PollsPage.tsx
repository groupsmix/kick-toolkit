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
  BarChart3,
  Plus,
  Vote,
  CheckCircle,
  XCircle,
  Clock,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface PollOption {
  option: string;
  index: number;
  votes: number;
  percentage: number;
}

interface Poll {
  id: string;
  channel: string;
  title: string;
  options: string[];
  duration_seconds: number;
  allow_multiple_votes: boolean;
  status: string;
  created_at: string;
  closed_at: string | null;
  total_votes?: number;
  results?: PollOption[];
}

export function PollsPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [polls, setPolls] = useState<Poll[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newOptions, setNewOptions] = useState(["", ""]);
  const [newDuration, setNewDuration] = useState(300);
  const [newAllowMultiple, setNewAllowMultiple] = useState(false);

  const fetchPolls = async () => {
    try {
      const data = await api<Poll[]>(`/api/polls/${channel}`);
      // Fetch results for each poll
      const withResults = await Promise.all(
        data.map(async (poll) => {
          try {
            const result = await api<Poll>(`/api/polls/${channel}/${poll.id}/results`);
            return { ...poll, ...result };
          } catch {
            return poll;
          }
        })
      );
      setPolls(withResults);
    } catch {
      toast.error("Failed to load polls");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolls();
  }, [channel]);

  const createPoll = async () => {
    const validOptions = newOptions.filter((o) => o.trim());
    if (!newTitle.trim() || validOptions.length < 2) {
      toast.error("Title and at least 2 options are required");
      return;
    }
    try {
      await api(`/api/polls/${channel}`, {
        method: "POST",
        body: JSON.stringify({
          title: newTitle,
          options: validOptions,
          duration_seconds: newDuration,
          allow_multiple_votes: newAllowMultiple,
        }),
      });
      toast.success("Poll created");
      setShowCreate(false);
      setNewTitle("");
      setNewOptions(["", ""]);
      fetchPolls();
    } catch {
      toast.error("Failed to create poll");
    }
  };

  const closePoll = async (pollId: string) => {
    try {
      await api(`/api/polls/${channel}/${pollId}/close`, { method: "POST" });
      toast.success("Poll closed");
      fetchPolls();
    } catch {
      toast.error("Failed to close poll");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const activePolls = polls.filter((p) => p.status === "active");
  const closedPolls = polls.filter((p) => p.status === "closed");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Vote className="w-6 h-6 text-blue-400" />
            Chat Polls & Voting
          </h2>
          <p className="text-sm text-zinc-500">Create polls for your viewers to vote on</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
          <Plus className="w-4 h-4 mr-2" />
          New Poll
        </Button>
      </div>

      {showCreate && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardHeader>
            <CardTitle className="text-white text-lg">Create New Poll</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-zinc-400 text-xs">Poll Question</Label>
              <Input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="What game should we play next?"
                className="bg-zinc-800 border-zinc-700 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-zinc-400 text-xs">Options</Label>
              {newOptions.map((opt, i) => (
                <div key={i} className="flex gap-2">
                  <Input
                    value={opt}
                    onChange={(e) => {
                      const updated = [...newOptions];
                      updated[i] = e.target.value;
                      setNewOptions(updated);
                    }}
                    placeholder={`Option ${i + 1}`}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                  {newOptions.length > 2 && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-zinc-500 hover:text-red-400"
                      onClick={() => setNewOptions(newOptions.filter((_, idx) => idx !== i))}
                    >
                      <XCircle className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              {newOptions.length < 10 && (
                <Button
                  variant="ghost"
                  className="text-zinc-400 text-sm"
                  onClick={() => setNewOptions([...newOptions, ""])}
                >
                  <Plus className="w-4 h-4 mr-1" /> Add Option
                </Button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-400 text-xs">Duration (seconds)</Label>
                <Input
                  type="number"
                  value={newDuration}
                  onChange={(e) => setNewDuration(parseInt(e.target.value) || 300)}
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <div className="flex items-center gap-3 pt-5">
                <Switch checked={newAllowMultiple} onCheckedChange={setNewAllowMultiple} />
                <Label className="text-zinc-400 text-sm">Allow multiple votes</Label>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setShowCreate(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={createPoll} className="bg-emerald-500 hover:bg-emerald-600 text-black">Create Poll</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="active" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="active" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Clock className="w-4 h-4 mr-2" />
            Active ({activePolls.length})
          </TabsTrigger>
          <TabsTrigger value="closed" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <CheckCircle className="w-4 h-4 mr-2" />
            Closed ({closedPolls.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4 mt-4">
          {activePolls.length === 0 ? (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Vote className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">No active polls. Create one to get started!</p>
              </CardContent>
            </Card>
          ) : (
            activePolls.map((poll) => (
              <PollCard key={poll.id} poll={poll} onClose={() => closePoll(poll.id)} />
            ))
          )}
        </TabsContent>

        <TabsContent value="closed" className="space-y-4 mt-4">
          {closedPolls.length === 0 ? (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <BarChart3 className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">No closed polls yet.</p>
              </CardContent>
            </Card>
          ) : (
            closedPolls.map((poll) => (
              <PollCard key={poll.id} poll={poll} />
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function PollCard({ poll, onClose }: { poll: Poll; onClose?: () => void }) {
  const results = poll.results || [];
  const totalVotes = poll.total_votes || 0;

  return (
    <Card className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-white font-semibold text-lg">{poll.title}</h3>
            <div className="flex items-center gap-2 mt-1">
              <Badge className={poll.status === "active" ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-700/50 text-zinc-400"}>
                {poll.status}
              </Badge>
              <span className="text-xs text-zinc-500">{totalVotes} votes</span>
              {poll.allow_multiple_votes && (
                <span className="text-xs text-zinc-500">Multi-vote</span>
              )}
            </div>
          </div>
          {poll.status === "active" && onClose && (
            <Button onClick={onClose} variant="outline" size="sm" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800">
              Close Poll
            </Button>
          )}
        </div>
        <div className="space-y-3">
          {results.length > 0
            ? results.map((r) => (
                <div key={r.index}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-zinc-300">{r.option}</span>
                    <span className="text-zinc-400">{r.votes} ({r.percentage}%)</span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-2.5">
                    <div
                      className="bg-blue-500 h-2.5 rounded-full transition-all duration-500"
                      style={{ width: `${r.percentage}%` }}
                    />
                  </div>
                </div>
              ))
            : (poll.options || []).map((opt, i) => (
                <div key={i}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-zinc-300">{opt}</span>
                    <span className="text-zinc-400">0 (0%)</span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-2.5" />
                </div>
              ))}
        </div>
      </CardContent>
    </Card>
  );
}
