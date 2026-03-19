import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  Calendar,
  Plus,
  Trash2,
  Clock,
  Gamepad2,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface ScheduleEntry {
  id: string;
  channel: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  title: string;
  game: string;
  recurring: boolean;
  enabled: boolean;
  created_at: string;
}

const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const DAY_COLORS = [
  "border-blue-500/20 bg-blue-500/5",
  "border-purple-500/20 bg-purple-500/5",
  "border-emerald-500/20 bg-emerald-500/5",
  "border-amber-500/20 bg-amber-500/5",
  "border-pink-500/20 bg-pink-500/5",
  "border-cyan-500/20 bg-cyan-500/5",
  "border-red-500/20 bg-red-500/5",
];

export function SchedulePage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [entries, setEntries] = useState<ScheduleEntry[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newEntry, setNewEntry] = useState({
    day_of_week: 0,
    start_time: "19:00",
    end_time: "23:00",
    title: "",
    game: "",
    recurring: true,
    enabled: true,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<ScheduleEntry[]>(`/api/schedule/${channel}`)
      .then(setEntries)
      .catch(() => toast.error("Failed to load schedule"))
      .finally(() => setLoading(false));
  }, [channel]);

  const addEntry = async () => {
    try {
      const result = await api<ScheduleEntry>(`/api/schedule/${channel}`, {
        method: "POST",
        body: JSON.stringify(newEntry),
      });
      setEntries([...entries, result].sort((a, b) => a.day_of_week - b.day_of_week));
      setNewEntry({ day_of_week: 0, start_time: "19:00", end_time: "23:00", title: "", game: "", recurring: true, enabled: true });
      setShowAdd(false);
      toast.success("Schedule entry added");
    } catch {
      toast.error("Failed to add entry");
    }
  };

  const deleteEntry = async (id: string) => {
    try {
      await api(`/api/schedule/${channel}/${id}`, { method: "DELETE" });
      setEntries(entries.filter((e) => e.id !== id));
      toast.success("Entry deleted");
    } catch {
      toast.error("Failed to delete entry");
    }
  };

  const toggleEntry = async (entry: ScheduleEntry) => {
    try {
      const result = await api<ScheduleEntry>(`/api/schedule/${channel}/${entry.id}`, {
        method: "PUT",
        body: JSON.stringify({ enabled: !entry.enabled }),
      });
      setEntries(entries.map((e) => (e.id === entry.id ? result : e)));
    } catch {
      toast.error("Failed to update entry");
    }
  };

  // Group entries by day
  const entriesByDay: Record<number, ScheduleEntry[]> = {};
  entries.forEach((entry) => {
    if (!entriesByDay[entry.day_of_week]) entriesByDay[entry.day_of_week] = [];
    entriesByDay[entry.day_of_week].push(entry);
  });

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
            <Calendar className="w-6 h-6 text-blue-400" />
            Stream Schedule
          </h2>
          <p className="text-sm text-zinc-500">Set your weekly streaming schedule</p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)} className="bg-emerald-500 hover:bg-emerald-600 text-black">
          <Plus className="w-4 h-4 mr-2" />
          Add Slot
        </Button>
      </div>

      {showAdd && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardContent className="p-4 space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label className="text-zinc-400 text-xs">Day</Label>
                <select
                  value={newEntry.day_of_week}
                  onChange={(e) => setNewEntry({ ...newEntry, day_of_week: parseInt(e.target.value) })}
                  className="w-full h-10 rounded-md border border-zinc-700 bg-zinc-800 text-white px-3 text-sm"
                >
                  {DAY_NAMES.map((day, i) => (
                    <option key={i} value={i}>{day}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Start Time (UTC)</Label>
                <Input type="time" value={newEntry.start_time} onChange={(e) => setNewEntry({ ...newEntry, start_time: e.target.value })} className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">End Time (UTC)</Label>
                <Input type="time" value={newEntry.end_time} onChange={(e) => setNewEntry({ ...newEntry, end_time: e.target.value })} className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-zinc-400 text-xs">Stream Title</Label>
                <Input value={newEntry.title} onChange={(e) => setNewEntry({ ...newEntry, title: e.target.value })} placeholder="Ranked grind!" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Game / Category</Label>
                <Input value={newEntry.game} onChange={(e) => setNewEntry({ ...newEntry, game: e.target.value })} placeholder="Valorant" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Switch checked={newEntry.recurring} onCheckedChange={(v) => setNewEntry({ ...newEntry, recurring: v })} />
                <Label className="text-zinc-400 text-xs">Recurring weekly</Label>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={() => setShowAdd(false)} className="text-zinc-400">Cancel</Button>
                <Button onClick={addEntry} className="bg-emerald-500 hover:bg-emerald-600 text-black">Add Slot</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Weekly calendar view */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {DAY_NAMES.map((dayName, dayIndex) => (
          <Card key={dayIndex} className={`border ${DAY_COLORS[dayIndex]} ${entriesByDay[dayIndex] ? "" : "opacity-50"}`}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-white flex items-center justify-between">
                {dayName}
                {entriesByDay[dayIndex] && (
                  <Badge variant="outline" className="text-[10px] border-emerald-500/30 text-emerald-400">
                    {entriesByDay[dayIndex].length} slot{entriesByDay[dayIndex].length > 1 ? "s" : ""}
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {entriesByDay[dayIndex] ? (
                entriesByDay[dayIndex].map((entry) => (
                  <div key={entry.id} className="p-2 rounded-lg bg-zinc-900/80 border border-zinc-800">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3 text-zinc-500" />
                        <span className="text-xs text-zinc-300 font-mono">{entry.start_time} - {entry.end_time}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Switch checked={entry.enabled} onCheckedChange={() => toggleEntry(entry)} />
                        <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-600 hover:text-red-400" onClick={() => deleteEntry(entry.id)}>
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                    {entry.title && <p className="text-xs text-white font-medium">{entry.title}</p>}
                    {entry.game && (
                      <div className="flex items-center gap-1 mt-1">
                        <Gamepad2 className="w-3 h-3 text-zinc-500" />
                        <span className="text-[10px] text-zinc-500">{entry.game}</span>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-xs text-zinc-600 text-center py-2">No streams scheduled</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
