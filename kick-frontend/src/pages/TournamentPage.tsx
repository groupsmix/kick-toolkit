import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  Trophy,
  Plus,
  Play,
  Users,
  Swords,
  Crown,
  UserPlus,
  Trash2,
  RotateCcw,
  Gamepad2,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface Participant {
  username: string;
  seed: number | null;
  eliminated: boolean;
}

interface Match {
  id: string;
  round: number;
  match_number: number;
  player1: string | null;
  player2: string | null;
  winner: string | null;
  status: string;
}

interface Tournament {
  id: string;
  name: string;
  channel: string;
  game: string;
  max_participants: number;
  format: string;
  keyword: string;
  status: string;
  participants: Participant[];
  matches: Match[];
  current_round: number;
  winner: string | null;
  created_at: string;
}

export function TournamentPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedTournament, setSelectedTournament] = useState<string | null>(null);
  const [batchNames, setBatchNames] = useState("");
  const [newTourney, setNewTourney] = useState({
    name: "",
    game: "",
    max_participants: 8,
    format: "single_elimination",
    keyword: "!join",
    entry_duration_seconds: 300,
    description: "",
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api<Tournament[]>(`/api/tournament?channel=${channel}`)
      .then((data) => {
        setTournaments(data);
        if (data.length > 0 && !selectedTournament) {
          setSelectedTournament(data[0].id);
        }
      })
      .catch((err) => {
        setError(err.message || "Failed to load tournaments");
        toast.error("Failed to load tournaments");
      })
      .finally(() => setLoading(false));
  }, [channel]);

  const selected = tournaments.find((t) => t.id === selectedTournament);

  const createTournament = async () => {
    if (!newTourney.name) return;
    const t = await api<Tournament>("/api/tournament/create", {
      method: "POST",
      body: JSON.stringify({ ...newTourney, channel }),
    });
    setTournaments([t, ...tournaments]);
    setSelectedTournament(t.id);
    setShowCreate(false);
    setNewTourney({ name: "", game: "", max_participants: 8, format: "single_elimination", keyword: "!join", entry_duration_seconds: 300, description: "" });
    toast.success(`Tournament "${t.name}" created`);
  };

  const registerBatch = async () => {
    if (!selected || !batchNames.trim()) return;
    const names = batchNames.split(/[,\n]/).map((n) => n.trim()).filter(Boolean);
    await api(`/api/tournament/${selected.id}/register-batch`, {
      method: "POST",
      body: JSON.stringify(names),
    });
    const updated = await api<Tournament>(`/api/tournament/${selected.id}`);
    setTournaments(tournaments.map((t) => (t.id === selected.id ? updated : t)));
    setBatchNames("");
  };

  const startTournament = async () => {
    if (!selected) return;
    const updated = await api<Tournament>(`/api/tournament/${selected.id}/start`, { method: "POST" });
    setTournaments(tournaments.map((t) => (t.id === selected.id ? updated : t)));
  };

  const setWinner = async (matchId: string, winner: string) => {
    if (!selected) return;
    const result = await api<{ tournament: Tournament }>(`/api/tournament/${selected.id}/match/${matchId}/winner?winner=${winner}`, {
      method: "POST",
    });
    setTournaments(tournaments.map((t) => (t.id === selected.id ? result.tournament : t)));
  };

  const resetTournament = async () => {
    if (!selected) return;
    const updated = await api<Tournament>(`/api/tournament/${selected.id}/reset`, { method: "POST" });
    setTournaments(tournaments.map((t) => (t.id === selected.id ? updated : t)));
  };

  const deleteTournament = async (id: string) => {
    try {
      await api(`/api/tournament/${id}`, { method: "DELETE" });
      setTournaments(tournaments.filter((t) => t.id !== id));
      if (selectedTournament === id) {
        setSelectedTournament(tournaments.find((t) => t.id !== id)?.id || null);
      }
      toast.success("Tournament deleted");
    } catch {
      toast.error("Failed to delete tournament");
    }
  };

  const statusColor = (status: string) => {
    if (status === "registration") return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    if (status === "in_progress") return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    if (status === "completed") return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    return "bg-zinc-500/10 text-zinc-400";
  };

  const matchStatusColor = (status: string) => {
    if (status === "completed") return "border-emerald-500/20 bg-emerald-500/5";
    if (status === "in_progress") return "border-amber-500/20 bg-amber-500/5";
    return "border-zinc-800";
  };

  const getRoundMatches = () => {
    if (!selected) return {};
    const rounds: Record<number, Match[]> = {};
    for (const match of selected.matches) {
      if (!rounds[match.round]) rounds[match.round] = [];
      rounds[match.round].push(match);
    }
    return rounds;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-zinc-400">{error}</p>
        <Button onClick={() => window.location.reload()} variant="outline" className="border-zinc-700 text-zinc-300">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Tournament Organizer</h3>
          <p className="text-sm text-zinc-500">
            Collect entries via keyword, auto-build brackets, manage matches
          </p>
        </div>
        <Button
          onClick={() => setShowCreate(!showCreate)}
          className="bg-emerald-500 hover:bg-emerald-600 text-black"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Tournament
        </Button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <Card className="bg-zinc-900/50 border-emerald-500/20">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Trophy className="w-5 h-5 text-amber-400" />
              Create Tournament
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-400 text-xs">Tournament Name</Label>
                <Input
                  value={newTourney.name}
                  onChange={(e) => setNewTourney({ ...newTourney, name: e.target.value })}
                  placeholder="Friday Night Fights"
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Game</Label>
                <Input
                  value={newTourney.game}
                  onChange={(e) => setNewTourney({ ...newTourney, game: e.target.value })}
                  placeholder="Street Fighter 6"
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Max Participants</Label>
                <Input
                  type="number"
                  value={newTourney.max_participants}
                  onChange={(e) => setNewTourney({ ...newTourney, max_participants: parseInt(e.target.value) })}
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Entry Keyword</Label>
                <Input
                  value={newTourney.keyword}
                  onChange={(e) => setNewTourney({ ...newTourney, keyword: e.target.value })}
                  placeholder="!join"
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setShowCreate(false)} className="text-zinc-400">
                Cancel
              </Button>
              <Button onClick={createTournament} className="bg-emerald-500 hover:bg-emerald-600 text-black">
                Create Tournament
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Tournament List */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-zinc-400">Tournaments</h4>
          {tournaments.map((t) => (
            <button
              key={t.id}
              onClick={() => setSelectedTournament(t.id)}
              className={`w-full text-left p-3 rounded-lg border transition-colors ${
                selectedTournament === t.id
                  ? "bg-zinc-800/50 border-emerald-500/30"
                  : "bg-zinc-900/50 border-zinc-800 hover:border-zinc-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-white">{t.name}</span>
                <Badge className={`text-[10px] ${statusColor(t.status)}`}>{t.status}</Badge>
              </div>
              <div className="flex items-center gap-2 mt-1 text-xs text-zinc-500">
                {t.game && (
                  <span className="flex items-center gap-1">
                    <Gamepad2 className="w-3 h-3" />
                    {t.game}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {t.participants.length}/{t.max_participants}
                </span>
              </div>
            </button>
          ))}
        </div>

        {/* Tournament Detail */}
        <div className="lg:col-span-3 space-y-4">
          {selected ? (
            <>
              {/* Header */}
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-xl font-bold text-white">{selected.name}</h3>
                        <Badge className={statusColor(selected.status)}>{selected.status}</Badge>
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-zinc-500">
                        {selected.game && <span>Game: {selected.game}</span>}
                        <span>Format: {selected.format.replace("_", " ")}</span>
                        <span>Keyword: <code className="text-emerald-400">{selected.keyword}</code></span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {selected.status === "registration" && selected.participants.length >= 2 && (
                        <Button onClick={startTournament} className="bg-amber-500 hover:bg-amber-600 text-black">
                          <Play className="w-4 h-4 mr-2" />
                          Start
                        </Button>
                      )}
                      {selected.status !== "registration" && (
                        <Button onClick={resetTournament} variant="outline" className="border-zinc-700 text-zinc-300">
                          <RotateCcw className="w-4 h-4 mr-2" />
                          Reset
                        </Button>
                      )}
                      <Button variant="ghost" size="icon" onClick={() => deleteTournament(selected.id)} className="text-zinc-500 hover:text-red-400">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Winner */}
                  {selected.winner && (
                    <div className="mt-4 p-4 rounded-lg bg-gradient-to-r from-amber-500/20 to-amber-500/5 border border-amber-500/20 flex items-center gap-3">
                      <Crown className="w-8 h-8 text-amber-400" />
                      <div>
                        <p className="text-xs text-zinc-500">Tournament Champion</p>
                        <p className="text-2xl font-bold text-amber-400">{selected.winner}</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Registration Phase - Batch Add */}
              {selected.status === "registration" && (
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader>
                    <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                      <UserPlus className="w-4 h-4 text-emerald-400" />
                      Add Participants (from chat keyword collection)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-xs text-zinc-500">
                      Paste usernames collected from chat (comma or newline separated). In production, the bot auto-collects these when viewers type <code className="text-emerald-400">{selected.keyword}</code>
                    </p>
                    <div className="flex gap-2">
                      <Input
                        value={batchNames}
                        onChange={(e) => setBatchNames(e.target.value)}
                        placeholder="player1, player2, player3..."
                        className="bg-zinc-800 border-zinc-700 text-white"
                        onKeyDown={(e) => e.key === "Enter" && registerBatch()}
                      />
                      <Button onClick={registerBatch} variant="outline" className="border-zinc-700 text-zinc-300">
                        <UserPlus className="w-4 h-4 mr-2" />
                        Add All
                      </Button>
                    </div>

                    {/* Current Participants */}
                    <div className="flex flex-wrap gap-2 mt-2">
                      {selected.participants.map((p) => (
                        <Badge key={p.username} variant="outline" className="border-zinc-700 text-zinc-300">
                          {p.username}
                        </Badge>
                      ))}
                    </div>
                    <p className="text-xs text-zinc-500">
                      {selected.participants.length}/{selected.max_participants} slots filled
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* Bracket View */}
              {selected.matches.length > 0 && (
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader>
                    <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                      <Swords className="w-4 h-4 text-amber-400" />
                      Bracket
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="w-full">
                      <div className="flex gap-8 pb-4 min-w-max">
                        {Object.entries(getRoundMatches()).map(([round, matches]) => (
                          <div key={round} className="space-y-4 min-w-[240px]">
                            <h4 className="text-xs font-medium text-zinc-500 uppercase tracking-wider text-center">
                              {parseInt(round) === Object.keys(getRoundMatches()).length
                                ? "Finals"
                                : parseInt(round) === Object.keys(getRoundMatches()).length - 1
                                ? "Semi-Finals"
                                : `Round ${round}`}
                            </h4>
                            <div className="space-y-3">
                              {matches.map((match) => (
                                <div
                                  key={match.id}
                                  className={`rounded-lg border p-3 ${matchStatusColor(match.status)}`}
                                >
                                  <div className="text-[10px] text-zinc-600 mb-2">
                                    Match {match.match_number}
                                  </div>
                                  {/* Player 1 */}
                                  <button
                                    onClick={() => match.player1 && match.player2 && !match.winner && setWinner(match.id, match.player1)}
                                    disabled={!match.player1 || !match.player2 || !!match.winner}
                                    className={`w-full flex items-center justify-between p-2 rounded mb-1 transition-colors ${
                                      match.winner === match.player1
                                        ? "bg-emerald-500/10 text-emerald-400"
                                        : match.winner && match.winner !== match.player1
                                        ? "bg-zinc-800/50 text-zinc-600 line-through"
                                        : "bg-zinc-800/30 text-zinc-300 hover:bg-zinc-800"
                                    }`}
                                  >
                                    <span className="text-sm font-medium">
                                      {match.player1 || "TBD"}
                                    </span>
                                    {match.winner === match.player1 && (
                                      <Trophy className="w-3 h-3 text-emerald-400" />
                                    )}
                                  </button>
                                  {/* VS */}
                                  <div className="text-center text-[10px] text-zinc-600 my-1">VS</div>
                                  {/* Player 2 */}
                                  <button
                                    onClick={() => match.player1 && match.player2 && !match.winner && setWinner(match.id, match.player2)}
                                    disabled={!match.player1 || !match.player2 || !!match.winner}
                                    className={`w-full flex items-center justify-between p-2 rounded transition-colors ${
                                      match.winner === match.player2
                                        ? "bg-emerald-500/10 text-emerald-400"
                                        : match.winner && match.winner !== match.player2
                                        ? "bg-zinc-800/50 text-zinc-600 line-through"
                                        : "bg-zinc-800/30 text-zinc-300 hover:bg-zinc-800"
                                    }`}
                                  >
                                    <span className="text-sm font-medium">
                                      {match.player2 || "TBD"}
                                    </span>
                                    {match.winner === match.player2 && (
                                      <Trophy className="w-3 h-3 text-emerald-400" />
                                    )}
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              )}

              {/* Participants List */}
              {selected.status !== "registration" && selected.participants.length > 0 && (
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader>
                    <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                      <Users className="w-4 h-4 text-blue-400" />
                      Participants ({selected.participants.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {selected.participants.map((p) => (
                        <Badge
                          key={p.username}
                          variant="outline"
                          className={`${
                            p.username === selected.winner
                              ? "border-amber-500/30 text-amber-400"
                              : p.eliminated
                              ? "border-red-500/20 text-red-400/50 line-through"
                              : "border-emerald-500/30 text-emerald-400"
                          }`}
                        >
                          {p.username === selected.winner && <Crown className="w-3 h-3 mr-1" />}
                          {p.username}
                          {p.seed && <span className="ml-1 text-zinc-600">#{p.seed}</span>}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <Trophy className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-500">Select a tournament or create a new one</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
