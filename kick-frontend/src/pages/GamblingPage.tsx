import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { DollarSign, Trash2, TrendingUp, TrendingDown, Ban, Star, CloudRain } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface SlotRequest { id: string; username: string; slot_name: string; note: string; status: string; position: number; }
interface BannedSlot { id: string; slot_name: string; reason: string; }
interface GamblingSession { id: string; start_balance: number; current_balance: number; total_wagered: number; biggest_win: number; biggest_loss: number; status: string; started_at: string; }
interface SlotRating { id: string; slot_name: string; username: string; rating: number; comment: string; }
interface SlotStat { slot_name: string; total_bets: number; net_profit: number; }
interface RainEvent { id: string; amount: number; currency: string; source: string; tip_count: number; created_at: string; }

export function GamblingPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [slotRequests, setSlotRequests] = useState<SlotRequest[]>([]);
  const [bannedSlots, setBannedSlots] = useState<BannedSlot[]>([]);
  const [activeSession, setActiveSession] = useState<GamblingSession | null>(null);
  const [slotStats, setSlotStats] = useState<SlotStat[]>([]);
  const [ratings, setRatings] = useState<SlotRating[]>([]);
  const [rainEvents, setRainEvents] = useState<RainEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [newBanSlot, setNewBanSlot] = useState("");
  const [newBanReason, setNewBanReason] = useState("");
  const [startBalance, setStartBalance] = useState(1000);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<SlotRequest[]>(`/api/gambling/slots/${channel}/requests`).catch(() => []),
      api<BannedSlot[]>(`/api/gambling/slots/${channel}/banned`).catch(() => []),
      api<GamblingSession>(`/api/gambling/sessions/${channel}/active`).catch(() => null),
      api<SlotStat[]>(`/api/gambling/slot-stats/${channel}`).catch(() => []),
      api<SlotRating[]>(`/api/gambling/ratings/${channel}`).catch(() => []),
      api<RainEvent[]>(`/api/gambling/rain/${channel}`).catch(() => []),
    ])
      .then(([sr, bs, sess, ss, rat, rain]) => {
        setSlotRequests(sr as SlotRequest[]);
        setBannedSlots(bs as BannedSlot[]);
        if (sess && (sess as GamblingSession).id) setActiveSession(sess as GamblingSession);
        setSlotStats(ss as SlotStat[]);
        setRatings(rat as SlotRating[]);
        setRainEvents(rain as RainEvent[]);
      })
      .finally(() => setLoading(false));
  }, [channel]);

  const banSlot = async () => {
    try {
      const result = await api<BannedSlot>(`/api/gambling/slots/${channel}/banned`, {
        method: "POST", body: JSON.stringify({ slot_name: newBanSlot, reason: newBanReason }),
      });
      setBannedSlots([...bannedSlots, result]);
      setNewBanSlot("");
      setNewBanReason("");
      toast.success("Slot banned");
    } catch { toast.error("Failed to ban slot"); }
  };

  const unbanSlot = async (id: string) => {
    try {
      await api(`/api/gambling/slots/${channel}/banned/${id}`, { method: "DELETE" });
      setBannedSlots(bannedSlots.filter((s) => s.id !== id));
      toast.success("Slot unbanned");
    } catch { toast.error("Failed to unban"); }
  };

  const startSession = async () => {
    try {
      const result = await api<GamblingSession>(`/api/gambling/sessions/${channel}`, {
        method: "POST", body: JSON.stringify({ start_balance: startBalance }),
      });
      setActiveSession(result);
      toast.success("Session started");
    } catch { toast.error("Failed to start session"); }
  };

  const endSession = async () => {
    if (!activeSession) return;
    try {
      await api(`/api/gambling/sessions/${channel}/${activeSession.id}/end`, { method: "POST" });
      setActiveSession(null);
      toast.success("Session ended");
    } catch { toast.error("Failed to end session"); }
  };

  const updateRequestStatus = async (id: string, status: string) => {
    try {
      const result = await api<SlotRequest>(`/api/gambling/slots/${channel}/requests/${id}/status?status=${status}`, { method: "POST" });
      setSlotRequests(slotRequests.map((r) => (r.id === id ? result : r)));
    } catch { toast.error("Failed to update"); }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const pnl = activeSession ? activeSession.current_balance - activeSession.start_balance : 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <DollarSign className="w-6 h-6 text-green-400" />
          Gambling Dashboard
        </h2>
        <p className="text-sm text-zinc-500">Manage your gambling stream tools</p>
      </div>

      <Tabs defaultValue="session" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="session">Session P&L</TabsTrigger>
          <TabsTrigger value="requests">Slot Requests</TabsTrigger>
          <TabsTrigger value="banned">Banned Slots</TabsTrigger>
          <TabsTrigger value="stats">Hot/Cold</TabsTrigger>
          <TabsTrigger value="ratings">Ratings</TabsTrigger>
          <TabsTrigger value="rain">Rain/Tips</TabsTrigger>
        </TabsList>

        <TabsContent value="session" className="space-y-4 mt-4">
          {activeSession ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4 text-center">
                  <p className={`text-2xl font-bold ${pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {pnl >= 0 ? "+" : ""}{pnl.toFixed(2)}
                  </p>
                  <p className="text-xs text-zinc-500">Session P&L</p>
                </CardContent>
              </Card>
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-white">{activeSession.current_balance.toFixed(2)}</p>
                  <p className="text-xs text-zinc-500">Current Balance</p>
                </CardContent>
              </Card>
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-emerald-400">{activeSession.biggest_win.toFixed(2)}</p>
                  <p className="text-xs text-zinc-500">Biggest Win</p>
                </CardContent>
              </Card>
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-red-400">{activeSession.biggest_loss.toFixed(2)}</p>
                  <p className="text-xs text-zinc-500">Biggest Loss</p>
                </CardContent>
              </Card>
              <div className="col-span-full flex justify-center">
                <Button variant="outline" onClick={endSession} className="border-red-500/30 text-red-400">End Session</Button>
              </div>
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-6 text-center space-y-4">
                <p className="text-zinc-400">No active session</p>
                <div className="flex items-center gap-3 justify-center">
                  <Input type="number" value={startBalance} onChange={(e) => setStartBalance(parseFloat(e.target.value) || 0)} placeholder="Start balance" className="bg-zinc-800 border-zinc-700 text-white w-40" />
                  <Button onClick={startSession} className="bg-emerald-500 hover:bg-emerald-600 text-black">Start Session</Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="requests" className="space-y-3 mt-4">
          {slotRequests.map((req) => (
            <Card key={req.id} className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="flex-1">
                  <p className="text-white font-medium">{req.slot_name}</p>
                  <p className="text-xs text-zinc-500">by {req.username}{req.note ? ` — ${req.note}` : ""}</p>
                </div>
                <Badge variant="outline" className="text-[10px]">{req.status}</Badge>
                {req.status === "pending" && (
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost" className="text-emerald-400 text-xs" onClick={() => updateRequestStatus(req.id, "approved")}>Approve</Button>
                    <Button size="sm" variant="ghost" className="text-red-400 text-xs" onClick={() => updateRequestStatus(req.id, "rejected")}>Reject</Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
          {slotRequests.length === 0 && <p className="text-center text-zinc-600 py-8">No slot requests.</p>}
        </TabsContent>

        <TabsContent value="banned" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 flex gap-3">
              <Input value={newBanSlot} onChange={(e) => setNewBanSlot(e.target.value)} placeholder="Slot name" className="bg-zinc-800 border-zinc-700 text-white" />
              <Input value={newBanReason} onChange={(e) => setNewBanReason(e.target.value)} placeholder="Reason" className="bg-zinc-800 border-zinc-700 text-white" />
              <Button onClick={banSlot} className="bg-red-500 hover:bg-red-600 text-white whitespace-nowrap">
                <Ban className="w-4 h-4 mr-1" /> Ban
              </Button>
            </CardContent>
          </Card>
          <div className="space-y-2">
            {bannedSlots.map((slot) => (
              <div key={slot.id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/80 border border-zinc-800">
                <div>
                  <span className="text-white text-sm">{slot.slot_name}</span>
                  {slot.reason && <span className="text-xs text-zinc-500 ml-2">({slot.reason})</span>}
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-600 hover:text-emerald-400" onClick={() => unbanSlot(slot.id)}>
                  <Trash2 className="w-3 h-3" />
                </Button>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="stats" className="space-y-3 mt-4">
          {slotStats.map((stat) => (
            <div key={stat.slot_name} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/80 border border-zinc-800">
              <div className="flex items-center gap-2">
                {stat.net_profit >= 0 ? <TrendingUp className="w-4 h-4 text-emerald-400" /> : <TrendingDown className="w-4 h-4 text-red-400" />}
                <span className="text-white text-sm">{stat.slot_name}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs text-zinc-500">{stat.total_bets} bets</span>
                <span className={`text-sm font-medium ${stat.net_profit >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {stat.net_profit >= 0 ? "+" : ""}{stat.net_profit.toFixed(2)}
                </span>
              </div>
            </div>
          ))}
          {slotStats.length === 0 && <p className="text-center text-zinc-600 py-8">No slot stats yet.</p>}
        </TabsContent>

        <TabsContent value="ratings" className="space-y-3 mt-4">
          {ratings.map((r) => (
            <div key={r.id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/80 border border-zinc-800">
              <div>
                <span className="text-white text-sm">{r.slot_name}</span>
                <span className="text-xs text-zinc-500 ml-2">by {r.username}</span>
              </div>
              <div className="flex items-center gap-1">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} className={`w-3 h-3 ${i < r.rating ? "text-amber-400 fill-amber-400" : "text-zinc-700"}`} />
                ))}
              </div>
            </div>
          ))}
          {ratings.length === 0 && <p className="text-center text-zinc-600 py-8">No ratings yet.</p>}
        </TabsContent>

        <TabsContent value="rain" className="space-y-3 mt-4">
          {rainEvents.map((rain) => (
            <div key={rain.id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/80 border border-zinc-800">
              <div className="flex items-center gap-2">
                <CloudRain className="w-4 h-4 text-blue-400" />
                <div>
                  <span className="text-white text-sm">{rain.amount.toFixed(2)} {rain.currency}</span>
                  <span className="text-xs text-zinc-500 ml-2">{rain.source}</span>
                </div>
              </div>
              <span className="text-xs text-zinc-600">{new Date(rain.created_at).toLocaleString()}</span>
            </div>
          ))}
          {rainEvents.length === 0 && <p className="text-center text-zinc-600 py-8">No rain/tip events yet.</p>}
        </TabsContent>
      </Tabs>
    </div>
  );
}
