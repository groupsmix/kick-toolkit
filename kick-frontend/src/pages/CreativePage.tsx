import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { Palette, Plus, ThumbsUp, CheckCircle, Users } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface ArtCommission { id: string; username: string; description: string; reference_url: string; style: string; size: string; price: number; status: string; }
interface TutorialRequest { id: string; username: string; topic: string; votes: number; status: string; }
interface CollabRequest { id: string; requester_username: string; requester_channel: string; proposal: string; status: string; }

export function CreativePage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [commissions, setCommissions] = useState<ArtCommission[]>([]);
  const [tutorials, setTutorials] = useState<TutorialRequest[]>([]);
  const [collabs, setCollabs] = useState<CollabRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [newComm, setNewComm] = useState({ username: "", description: "", reference_url: "", style: "", size: "", price: 0 });
  const [newTutorial, setNewTutorial] = useState({ username: "", topic: "" });
  const [newCollab, setNewCollab] = useState({ requester_username: "", requester_channel: "", proposal: "" });
  const [showAddComm, setShowAddComm] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<ArtCommission[]>(`/api/creative/commissions/${channel}`).catch(() => []),
      api<TutorialRequest[]>(`/api/creative/tutorials/${channel}`).catch(() => []),
      api<CollabRequest[]>(`/api/creative/collabs/${channel}`).catch(() => []),
    ])
      .then(([c, t, co]) => {
        setCommissions(c as ArtCommission[]);
        setTutorials(t as TutorialRequest[]);
        setCollabs(co as CollabRequest[]);
      })
      .finally(() => setLoading(false));
  }, [channel]);

  const createCommission = async () => {
    try {
      const result = await api<ArtCommission>(`/api/creative/commissions/${channel}`, { method: "POST", body: JSON.stringify(newComm) });
      setCommissions([result, ...commissions]);
      setNewComm({ username: "", description: "", reference_url: "", style: "", size: "", price: 0 });
      setShowAddComm(false);
      toast.success("Commission created");
    } catch { toast.error("Failed to create"); }
  };

  const updateCommissionStatus = async (id: string, status: string) => {
    try {
      const result = await api<ArtCommission>(`/api/creative/commissions/${channel}/${id}/status?status=${status}`, { method: "POST" });
      setCommissions(commissions.map((c) => (c.id === id ? result : c)));
    } catch { toast.error("Failed to update"); }
  };

  const createTutorial = async () => {
    try {
      const result = await api<TutorialRequest>(`/api/creative/tutorials/${channel}`, { method: "POST", body: JSON.stringify(newTutorial) });
      setTutorials([result, ...tutorials]);
      setNewTutorial({ username: "", topic: "" });
      toast.success("Tutorial request added");
    } catch { toast.error("Failed to create"); }
  };

  const voteTutorial = async (id: string) => {
    try {
      const result = await api<TutorialRequest>(`/api/creative/tutorials/${channel}/${id}/vote`, { method: "POST" });
      setTutorials(tutorials.map((t) => (t.id === id ? result : t)));
    } catch { toast.error("Failed to vote"); }
  };

  const completeTutorial = async (id: string) => {
    try {
      const result = await api<TutorialRequest>(`/api/creative/tutorials/${channel}/${id}/complete`, { method: "POST" });
      setTutorials(tutorials.map((t) => (t.id === id ? result : t)));
    } catch { toast.error("Failed to complete"); }
  };

  const createCollab = async () => {
    try {
      const result = await api<CollabRequest>(`/api/creative/collabs/${channel}`, { method: "POST", body: JSON.stringify(newCollab) });
      setCollabs([result, ...collabs]);
      setNewCollab({ requester_username: "", requester_channel: "", proposal: "" });
      toast.success("Collab request created");
    } catch { toast.error("Failed to create"); }
  };

  const updateCollabStatus = async (id: string, status: string) => {
    try {
      const result = await api<CollabRequest>(`/api/creative/collabs/${channel}/${id}/status?status=${status}`, { method: "POST" });
      setCollabs(collabs.map((c) => (c.id === id ? result : c)));
    } catch { toast.error("Failed to update"); }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const statusColor: Record<string, string> = {
    pending: "border-amber-500/30 text-amber-400",
    accepted: "border-blue-500/30 text-blue-400",
    in_progress: "border-purple-500/30 text-purple-400",
    completed: "border-emerald-500/30 text-emerald-400",
    rejected: "border-zinc-700 text-zinc-500",
    cancelled: "border-zinc-700 text-zinc-500",
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Palette className="w-6 h-6 text-pink-400" />
          Creative / Music Tools
        </h2>
        <p className="text-sm text-zinc-500">Manage commissions, tutorials, and collaborations</p>
      </div>

      <Tabs defaultValue="commissions" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="commissions">Art Commissions</TabsTrigger>
          <TabsTrigger value="tutorials">Tutorial Requests</TabsTrigger>
          <TabsTrigger value="collabs">Collaborations</TabsTrigger>
        </TabsList>

        <TabsContent value="commissions" className="space-y-4 mt-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowAddComm(!showAddComm)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
              <Plus className="w-4 h-4 mr-2" /> New Commission
            </Button>
          </div>
          {showAddComm && (
            <Card className="bg-zinc-900/50 border-emerald-500/20">
              <CardContent className="p-4 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-zinc-400 text-xs">Username</Label>
                    <Input value={newComm.username} onChange={(e) => setNewComm({ ...newComm, username: e.target.value })} className="bg-zinc-800 border-zinc-700 text-white" />
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">Style</Label>
                    <Input value={newComm.style} onChange={(e) => setNewComm({ ...newComm, style: e.target.value })} placeholder="Anime, Realistic, etc." className="bg-zinc-800 border-zinc-700 text-white" />
                  </div>
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Description</Label>
                  <Input value={newComm.description} onChange={(e) => setNewComm({ ...newComm, description: e.target.value })} className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <Label className="text-zinc-400 text-xs">Reference URL</Label>
                    <Input value={newComm.reference_url} onChange={(e) => setNewComm({ ...newComm, reference_url: e.target.value })} className="bg-zinc-800 border-zinc-700 text-white" />
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">Size</Label>
                    <Input value={newComm.size} onChange={(e) => setNewComm({ ...newComm, size: e.target.value })} placeholder="1920x1080" className="bg-zinc-800 border-zinc-700 text-white" />
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">Price</Label>
                    <Input type="number" value={newComm.price} onChange={(e) => setNewComm({ ...newComm, price: parseFloat(e.target.value) || 0 })} className="bg-zinc-800 border-zinc-700 text-white" />
                  </div>
                </div>
                <div className="flex gap-2 justify-end">
                  <Button variant="ghost" onClick={() => setShowAddComm(false)} className="text-zinc-400">Cancel</Button>
                  <Button onClick={createCommission} className="bg-emerald-500 hover:bg-emerald-600 text-black">Create</Button>
                </div>
              </CardContent>
            </Card>
          )}
          {commissions.map((comm) => (
            <Card key={comm.id} className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4 flex items-start gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-white font-medium">{comm.description || "Commission"}</span>
                    <Badge variant="outline" className={`text-[10px] ${statusColor[comm.status] || ""}`}>{comm.status}</Badge>
                    {comm.price > 0 && <Badge variant="outline" className="text-[10px] border-emerald-500/30 text-emerald-400">${comm.price}</Badge>}
                  </div>
                  <p className="text-xs text-zinc-500">by {comm.username}{comm.style ? ` | ${comm.style}` : ""}{comm.size ? ` | ${comm.size}` : ""}</p>
                </div>
                {comm.status === "pending" && (
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost" className="text-emerald-400 text-xs" onClick={() => updateCommissionStatus(comm.id, "accepted")}>Accept</Button>
                    <Button size="sm" variant="ghost" className="text-red-400 text-xs" onClick={() => updateCommissionStatus(comm.id, "rejected")}>Reject</Button>
                  </div>
                )}
                {comm.status === "accepted" && (
                  <Button size="sm" variant="ghost" className="text-blue-400 text-xs" onClick={() => updateCommissionStatus(comm.id, "in_progress")}>Start</Button>
                )}
                {comm.status === "in_progress" && (
                  <Button size="sm" variant="ghost" className="text-emerald-400 text-xs" onClick={() => updateCommissionStatus(comm.id, "completed")}>Complete</Button>
                )}
              </CardContent>
            </Card>
          ))}
          {commissions.length === 0 && <p className="text-center text-zinc-600 py-8">No commissions yet.</p>}
        </TabsContent>

        <TabsContent value="tutorials" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 flex gap-3">
              <Input value={newTutorial.username} onChange={(e) => setNewTutorial({ ...newTutorial, username: e.target.value })} placeholder="Username" className="bg-zinc-800 border-zinc-700 text-white w-40" />
              <Input value={newTutorial.topic} onChange={(e) => setNewTutorial({ ...newTutorial, topic: e.target.value })} placeholder="Tutorial topic" className="bg-zinc-800 border-zinc-700 text-white" />
              <Button onClick={createTutorial} className="bg-emerald-500 hover:bg-emerald-600 text-black whitespace-nowrap">
                <Plus className="w-4 h-4 mr-1" /> Add
              </Button>
            </CardContent>
          </Card>
          {tutorials.sort((a, b) => b.votes - a.votes).map((tut) => (
            <Card key={tut.id} className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="flex-1">
                  <p className="text-white text-sm">{tut.topic}</p>
                  <p className="text-[10px] text-zinc-500">by {tut.username}</p>
                </div>
                <Badge variant="outline" className={`text-[10px] ${statusColor[tut.status] || ""}`}>{tut.status}</Badge>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" className="text-blue-400 text-xs" onClick={() => voteTutorial(tut.id)}>
                    <ThumbsUp className="w-3 h-3 mr-1" /> {tut.votes}
                  </Button>
                  {tut.status === "pending" && (
                    <Button variant="ghost" size="sm" className="text-emerald-400 text-xs" onClick={() => completeTutorial(tut.id)}>
                      <CheckCircle className="w-3 h-3 mr-1" /> Done
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
          {tutorials.length === 0 && <p className="text-center text-zinc-600 py-8">No tutorial requests yet.</p>}
        </TabsContent>

        <TabsContent value="collabs" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <Input value={newCollab.requester_username} onChange={(e) => setNewCollab({ ...newCollab, requester_username: e.target.value })} placeholder="Username" className="bg-zinc-800 border-zinc-700 text-white" />
                <Input value={newCollab.requester_channel} onChange={(e) => setNewCollab({ ...newCollab, requester_channel: e.target.value })} placeholder="Channel" className="bg-zinc-800 border-zinc-700 text-white" />
                <Input value={newCollab.proposal} onChange={(e) => setNewCollab({ ...newCollab, proposal: e.target.value })} placeholder="Proposal" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div className="flex justify-end">
                <Button onClick={createCollab} className="bg-emerald-500 hover:bg-emerald-600 text-black">
                  <Users className="w-4 h-4 mr-2" /> Request Collab
                </Button>
              </div>
            </CardContent>
          </Card>
          {collabs.map((collab) => (
            <Card key={collab.id} className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4 flex items-start gap-4">
                <Users className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-white text-sm">{collab.proposal}</p>
                  <p className="text-[10px] text-zinc-500">{collab.requester_username} ({collab.requester_channel})</p>
                </div>
                <Badge variant="outline" className={`text-[10px] ${statusColor[collab.status] || ""}`}>{collab.status}</Badge>
                {collab.status === "pending" && (
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost" className="text-emerald-400 text-xs" onClick={() => updateCollabStatus(collab.id, "accepted")}>Accept</Button>
                    <Button size="sm" variant="ghost" className="text-red-400 text-xs" onClick={() => updateCollabStatus(collab.id, "rejected")}>Reject</Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
          {collabs.length === 0 && <p className="text-center text-zinc-600 py-8">No collaboration requests yet.</p>}
        </TabsContent>
      </Tabs>
    </div>
  );
}
