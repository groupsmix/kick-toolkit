import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { MapPin, Plus, Trash2, MessageCircle, Camera, RotateCcw, Clock, Target } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface DonationGoal { id: string; title: string; target_amount: number; current_amount: number; currency: string; }
interface Question { id: string; username: string; question: string; status: string; priority: number; }
interface PhotoRequest { id: string; username: string; description: string; tip_amount: number; status: string; }
interface WheelChallenge { id: string; challenge_text: string; username: string; used: boolean; }
interface CountdownTimer { id: string; title: string; end_time: string; active: boolean; style: string; }

export function IRLPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [location, setLocation] = useState({ city: "", country: "" });
  const [goals, setGoals] = useState<DonationGoal[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [photoRequests, setPhotoRequests] = useState<PhotoRequest[]>([]);
  const [wheelChallenges, setWheelChallenges] = useState<WheelChallenge[]>([]);
  const [timers, setTimers] = useState<CountdownTimer[]>([]);
  const [loading, setLoading] = useState(true);
  const [spinResult, setSpinResult] = useState<WheelChallenge | null>(null);
  const [newGoal, setNewGoal] = useState({ title: "", target_amount: 100, currency: "USD" });
  const [newChallenge, setNewChallenge] = useState("");
  const [newTimerTitle, setNewTimerTitle] = useState("");
  const [newTimerEnd, setNewTimerEnd] = useState("");

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<{ city: string; country: string }>(`/api/irl/location/${channel}`).catch(() => ({ city: "", country: "" })),
      api<DonationGoal[]>(`/api/irl/goals/${channel}`).catch(() => []),
      api<Question[]>(`/api/irl/questions/${channel}`).catch(() => []),
      api<PhotoRequest[]>(`/api/irl/photos/${channel}`).catch(() => []),
      api<WheelChallenge[]>(`/api/irl/wheel/${channel}`).catch(() => []),
      api<CountdownTimer[]>(`/api/irl/timers/${channel}`).catch(() => []),
    ])
      .then(([loc, g, q, p, w, t]) => {
        setLocation(loc as { city: string; country: string });
        setGoals(g as DonationGoal[]);
        setQuestions(q as Question[]);
        setPhotoRequests(p as PhotoRequest[]);
        setWheelChallenges(w as WheelChallenge[]);
        setTimers(t as CountdownTimer[]);
      })
      .finally(() => setLoading(false));
  }, [channel]);

  const updateLocation = async () => {
    try {
      await api(`/api/irl/location/${channel}`, { method: "POST", body: JSON.stringify(location) });
      toast.success("Location updated");
    } catch { toast.error("Failed to update location"); }
  };

  const createGoal = async () => {
    try {
      const result = await api<DonationGoal>(`/api/irl/goals/${channel}`, { method: "POST", body: JSON.stringify(newGoal) });
      setGoals([...goals, result]);
      setNewGoal({ title: "", target_amount: 100, currency: "USD" });
      toast.success("Goal created");
    } catch { toast.error("Failed to create goal"); }
  };

  const deleteGoal = async (id: string) => {
    try {
      await api(`/api/irl/goals/${channel}/${id}`, { method: "DELETE" });
      setGoals(goals.filter((g) => g.id !== id));
    } catch { toast.error("Failed to delete"); }
  };

  const updateQuestionStatus = async (id: string, status: string) => {
    try {
      const result = await api<Question>(`/api/irl/questions/${channel}/${id}/status?status=${status}`, { method: "POST" });
      setQuestions(questions.map((q) => (q.id === id ? result : q)));
    } catch { toast.error("Failed to update"); }
  };

  const updatePhotoStatus = async (id: string, status: string) => {
    try {
      const result = await api<PhotoRequest>(`/api/irl/photos/${channel}/${id}/status?status=${status}`, { method: "POST" });
      setPhotoRequests(photoRequests.map((p) => (p.id === id ? result : p)));
    } catch { toast.error("Failed to update"); }
  };

  const addChallenge = async () => {
    try {
      const result = await api<WheelChallenge>(`/api/irl/wheel/${channel}`, {
        method: "POST", body: JSON.stringify({ challenge_text: newChallenge, username: user?.name || "" }),
      });
      setWheelChallenges([...wheelChallenges, result]);
      setNewChallenge("");
    } catch { toast.error("Failed to add challenge"); }
  };

  const spinWheel = async () => {
    try {
      const result = await api<WheelChallenge>(`/api/irl/wheel/${channel}/spin`, { method: "POST" });
      setSpinResult(result);
      toast.success("Wheel spun!");
    } catch { toast.error("No unused challenges available"); }
  };

  const createTimer = async () => {
    try {
      const result = await api<CountdownTimer>(`/api/irl/timers/${channel}`, {
        method: "POST", body: JSON.stringify({ title: newTimerTitle, end_time: newTimerEnd, style: "default" }),
      });
      setTimers([...timers, result]);
      setNewTimerTitle("");
      setNewTimerEnd("");
    } catch { toast.error("Failed to create timer"); }
  };

  const deleteTimer = async (id: string) => {
    try {
      await api(`/api/irl/timers/${channel}/${id}`, { method: "DELETE" });
      setTimers(timers.filter((t) => t.id !== id));
    } catch { toast.error("Failed to delete"); }
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
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <MapPin className="w-6 h-6 text-red-400" />
          IRL Stream Tools
        </h2>
        <p className="text-sm text-zinc-500">Tools for IRL streaming</p>
      </div>

      <Tabs defaultValue="location" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="location">Location</TabsTrigger>
          <TabsTrigger value="goals">Donation Goals</TabsTrigger>
          <TabsTrigger value="questions">Questions</TabsTrigger>
          <TabsTrigger value="photos">Photos</TabsTrigger>
          <TabsTrigger value="wheel">Challenge Wheel</TabsTrigger>
          <TabsTrigger value="timers">Timers</TabsTrigger>
        </TabsList>

        <TabsContent value="location" className="mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-zinc-400 text-xs">City</Label>
                  <Input value={location.city} onChange={(e) => setLocation({ ...location, city: e.target.value })} className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Country</Label>
                  <Input value={location.country} onChange={(e) => setLocation({ ...location, country: e.target.value })} className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
              </div>
              <Button onClick={updateLocation} className="bg-emerald-500 hover:bg-emerald-600 text-black">Update Location</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="goals" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 flex gap-3">
              <Input value={newGoal.title} onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })} placeholder="Goal title" className="bg-zinc-800 border-zinc-700 text-white" />
              <Input type="number" value={newGoal.target_amount} onChange={(e) => setNewGoal({ ...newGoal, target_amount: parseFloat(e.target.value) || 0 })} placeholder="Target" className="bg-zinc-800 border-zinc-700 text-white w-32" />
              <Button onClick={createGoal} className="bg-emerald-500 hover:bg-emerald-600 text-black whitespace-nowrap">
                <Plus className="w-4 h-4 mr-1" /> Add
              </Button>
            </CardContent>
          </Card>
          {goals.map((goal) => {
            const pct = goal.target_amount > 0 ? Math.min(100, (goal.current_amount / goal.target_amount) * 100) : 0;
            return (
              <Card key={goal.id} className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-white font-medium">{goal.title}</h3>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-zinc-400">{goal.current_amount.toFixed(2)} / {goal.target_amount.toFixed(2)} {goal.currency}</span>
                      <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-600 hover:text-red-400" onClick={() => deleteGoal(goal.id)}>
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                  <Progress value={pct} className="h-3" />
                </CardContent>
              </Card>
            );
          })}
        </TabsContent>

        <TabsContent value="questions" className="space-y-3 mt-4">
          {questions.map((q) => (
            <Card key={q.id} className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4 flex items-center gap-4">
                <MessageCircle className="w-4 h-4 text-blue-400 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-white text-sm">{q.question}</p>
                  <p className="text-[10px] text-zinc-500">from {q.username}</p>
                </div>
                <Badge variant="outline" className="text-[10px]">{q.status}</Badge>
                {q.status === "pending" && (
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost" className="text-emerald-400 text-xs" onClick={() => updateQuestionStatus(q.id, "answered")}>Answer</Button>
                    <Button size="sm" variant="ghost" className="text-red-400 text-xs" onClick={() => updateQuestionStatus(q.id, "skipped")}>Skip</Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
          {questions.length === 0 && <p className="text-center text-zinc-600 py-8">No questions yet.</p>}
        </TabsContent>

        <TabsContent value="photos" className="space-y-3 mt-4">
          {photoRequests.map((p) => (
            <Card key={p.id} className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4 flex items-center gap-4">
                <Camera className="w-4 h-4 text-pink-400 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-white text-sm">{p.description}</p>
                  <p className="text-[10px] text-zinc-500">from {p.username} {p.tip_amount > 0 ? `($${p.tip_amount.toFixed(2)} tip)` : ""}</p>
                </div>
                <Badge variant="outline" className="text-[10px]">{p.status}</Badge>
                {p.status === "pending" && (
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost" className="text-emerald-400 text-xs" onClick={() => updatePhotoStatus(p.id, "approved")}>Approve</Button>
                    <Button size="sm" variant="ghost" className="text-red-400 text-xs" onClick={() => updatePhotoStatus(p.id, "rejected")}>Reject</Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
          {photoRequests.length === 0 && <p className="text-center text-zinc-600 py-8">No photo requests yet.</p>}
        </TabsContent>

        <TabsContent value="wheel" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 flex gap-3">
              <Input value={newChallenge} onChange={(e) => setNewChallenge(e.target.value)} placeholder="Challenge text" className="bg-zinc-800 border-zinc-700 text-white" />
              <Button onClick={addChallenge} className="bg-emerald-500 hover:bg-emerald-600 text-black whitespace-nowrap">
                <Plus className="w-4 h-4 mr-1" /> Add
              </Button>
              <Button onClick={spinWheel} className="bg-amber-500 hover:bg-amber-600 text-black whitespace-nowrap">
                <RotateCcw className="w-4 h-4 mr-1" /> Spin!
              </Button>
            </CardContent>
          </Card>
          {spinResult && (
            <Card className="bg-amber-500/10 border-amber-500/30">
              <CardContent className="p-4 text-center">
                <Target className="w-8 h-8 text-amber-400 mx-auto mb-2" />
                <p className="text-lg font-bold text-white">{spinResult.challenge_text}</p>
                <p className="text-xs text-zinc-500 mt-1">from {spinResult.username}</p>
              </CardContent>
            </Card>
          )}
          <div className="space-y-2">
            {wheelChallenges.map((ch) => (
              <div key={ch.id} className={`flex items-center justify-between p-3 rounded-lg bg-zinc-900/80 border border-zinc-800 ${ch.used ? "opacity-50" : ""}`}>
                <span className="text-white text-sm">{ch.challenge_text}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-zinc-500">{ch.username}</span>
                  {ch.used && <Badge variant="outline" className="text-[10px] border-zinc-700">Used</Badge>}
                </div>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="timers" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 flex gap-3">
              <Input value={newTimerTitle} onChange={(e) => setNewTimerTitle(e.target.value)} placeholder="Timer title" className="bg-zinc-800 border-zinc-700 text-white" />
              <Input type="datetime-local" value={newTimerEnd} onChange={(e) => setNewTimerEnd(e.target.value)} className="bg-zinc-800 border-zinc-700 text-white" />
              <Button onClick={createTimer} className="bg-emerald-500 hover:bg-emerald-600 text-black whitespace-nowrap">
                <Plus className="w-4 h-4 mr-1" /> Add
              </Button>
            </CardContent>
          </Card>
          {timers.map((t) => (
            <Card key={t.id} className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-blue-400" />
                  <div>
                    <p className="text-white font-medium">{t.title}</p>
                    <p className="text-xs text-zinc-500">Ends: {new Date(t.end_time).toLocaleString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className={`text-[10px] ${t.active ? "border-emerald-500/30 text-emerald-400" : "border-zinc-700 text-zinc-500"}`}>
                    {t.active ? "Active" : "Paused"}
                  </Badge>
                  <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-600 hover:text-red-400" onClick={() => deleteTimer(t.id)}>
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}
