import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { Timer, Plus, Trash2 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface TimedMessage {
  id: string;
  channel: string;
  message: string;
  interval_minutes: number;
  enabled: boolean;
  created_at: string;
}

export function TimedMessagesPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [messages, setMessages] = useState<TimedMessage[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newMsg, setNewMsg] = useState({ message: "", interval_minutes: 10, enabled: true });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<TimedMessage[]>(`/api/timed-messages/${channel}`)
      .then(setMessages)
      .catch(() => toast.error("Failed to load timed messages"))
      .finally(() => setLoading(false));
  }, [channel]);

  const addMessage = async () => {
    try {
      const result = await api<TimedMessage>(`/api/timed-messages/${channel}`, {
        method: "POST",
        body: JSON.stringify(newMsg),
      });
      setMessages([...messages, result]);
      setNewMsg({ message: "", interval_minutes: 10, enabled: true });
      setShowAdd(false);
      toast.success("Timed message added");
    } catch {
      toast.error("Failed to add message");
    }
  };

  const deleteMessage = async (id: string) => {
    try {
      await api(`/api/timed-messages/${channel}/${id}`, { method: "DELETE" });
      setMessages(messages.filter((m) => m.id !== id));
      toast.success("Message deleted");
    } catch {
      toast.error("Failed to delete");
    }
  };

  const toggleMessage = async (msg: TimedMessage) => {
    try {
      const result = await api<TimedMessage>(`/api/timed-messages/${channel}/${msg.id}`, {
        method: "PUT",
        body: JSON.stringify({ enabled: !msg.enabled }),
      });
      setMessages(messages.map((m) => (m.id === msg.id ? result : m)));
    } catch {
      toast.error("Failed to update");
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
            <Timer className="w-6 h-6 text-blue-400" />
            Timed Messages
          </h2>
          <p className="text-sm text-zinc-500">Auto-post messages at set intervals</p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
          <Plus className="w-4 h-4 mr-2" />
          Add Message
        </Button>
      </div>

      {showAdd && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardContent className="p-4 space-y-3">
            <div>
              <Label className="text-zinc-400 text-xs">Message</Label>
              <Input
                value={newMsg.message}
                onChange={(e) => setNewMsg({ ...newMsg, message: e.target.value })}
                placeholder="Follow the stream for more content!"
                className="bg-zinc-800 border-zinc-700 text-white"
              />
            </div>
            <div className="flex items-center gap-4">
              <div className="w-48">
                <Label className="text-zinc-400 text-xs">Interval (minutes)</Label>
                <Input
                  type="number"
                  value={newMsg.interval_minutes}
                  onChange={(e) => setNewMsg({ ...newMsg, interval_minutes: parseInt(e.target.value) || 5 })}
                  min={1}
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <div className="flex gap-2 ml-auto">
                <Button variant="ghost" onClick={() => setShowAdd(false)} className="text-zinc-400">Cancel</Button>
                <Button onClick={addMessage} className="bg-emerald-500 hover:bg-emerald-600 text-black">Add</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {messages.map((msg) => (
          <Card key={msg.id} className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 flex items-center gap-4">
              <div className="flex-1">
                <p className="text-sm text-white">{msg.message}</p>
                <Badge variant="outline" className="mt-1 text-[10px] border-zinc-700 text-zinc-400">
                  Every {msg.interval_minutes} min
                </Badge>
              </div>
              <Switch checked={msg.enabled} onCheckedChange={() => toggleMessage(msg)} />
              <Button variant="ghost" size="icon" className="text-zinc-600 hover:text-red-400" onClick={() => deleteMessage(msg.id)}>
                <Trash2 className="w-4 h-4" />
              </Button>
            </CardContent>
          </Card>
        ))}
        {messages.length === 0 && (
          <p className="text-center text-zinc-600 py-8">No timed messages yet. Add one to get started.</p>
        )}
      </div>
    </div>
  );
}
