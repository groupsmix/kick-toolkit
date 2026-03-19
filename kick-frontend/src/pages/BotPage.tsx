import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  Bot,
  Plus,
  Trash2,
  Shield,
  AlertTriangle,
  MessageSquare,
  Send,
  Lock,
  Clock,
  UserCheck,
  Megaphone,
  Variable,
  Eye,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface BotCommand {
  name: string;
  response: string;
  cooldown: number;
  enabled: boolean;
  mod_only: boolean;
}

interface ModRule {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  action: string;
  severity: number;
  settings: Record<string, unknown>;
}

interface ModerationResult {
  flagged: boolean;
  reason: string | null;
  action: string | null;
  confidence: number;
}

interface TimedMsg {
  id: string;
  channel: string;
  message: string;
  interval_minutes: number;
  enabled: boolean;
  created_at: string;
}

interface CommandVar {
  name: string;
  description: string;
}

interface BotConfigData {
  channel: string;
  prefix: string;
  enabled: boolean;
  welcome_message: string | null;
  auto_mod_enabled: boolean;
  welcome_enabled: boolean;
  welcome_new_message: string | null;
  welcome_returning_message: string | null;
  welcome_subscriber_message: string | null;
  shoutout_template: string;
  auto_shoutout_raiders: boolean;
}

interface ShoutoutResultData {
  target_username: string;
  message: string;
  avatar_url: string | null;
  is_live: boolean;
  game: string | null;
  title: string | null;
  follower_count: number;
}

export function BotPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [commands, setCommands] = useState<BotCommand[]>([]);
  const [modRules, setModRules] = useState<ModRule[]>([]);
  const [newCmd, setNewCmd] = useState({ name: "", response: "", cooldown: 5, mod_only: false });
  const [testMessage, setTestMessage] = useState("");
  const [modResult, setModResult] = useState<ModerationResult | null>(null);
  const [showAddCmd, setShowAddCmd] = useState(false);

  const [timedMessages, setTimedMessages] = useState<TimedMsg[]>([]);
  const [showAddTimed, setShowAddTimed] = useState(false);
  const [newTimed, setNewTimed] = useState({ message: "", interval_minutes: 15 });

  const [botConfig, setBotConfig] = useState<BotConfigData | null>(null);
  const [commandVars, setCommandVars] = useState<CommandVar[]>([]);

  const [shoutoutTarget, setShoutoutTarget] = useState("");
  const [shoutoutResult, setShoutoutResult] = useState<ShoutoutResultData | null>(null);

  const [previewCmd, setPreviewCmd] = useState("");
  const [previewResult, setPreviewResult] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<BotCommand[]>(`/api/bot/commands/${channel}`).then(setCommands),
      api<ModRule[]>(`/api/moderation/rules/${channel}`).then(setModRules),
      api<TimedMsg[]>(`/api/bot/timed/${channel}`).then(setTimedMessages),
      api<BotConfigData>(`/api/bot/config/${channel}`).then(setBotConfig),
      api<CommandVar[]>("/api/bot/commands/variables/list").then(setCommandVars),
    ])
      .catch((err) => {
        setError(err.message || "Failed to load bot data");
        toast.error("Failed to load bot data");
      })
      .finally(() => setLoading(false));
  }, [channel]);

  const addCommand = async () => {
    if (!newCmd.name || !newCmd.response) return;
    const cmd = await api<BotCommand>(`/api/bot/commands/${channel}`, {
      method: "POST",
      body: JSON.stringify({ ...newCmd, enabled: true }),
    });
    setCommands([...commands, cmd]);
    setNewCmd({ name: "", response: "", cooldown: 5, mod_only: false });
    setShowAddCmd(false);
    toast.success(`Command !${cmd.name} added`);
  };

  const deleteCommand = async (name: string) => {
    try {
      await api(`/api/bot/commands/${channel}/${name}`, { method: "DELETE" });
      setCommands(commands.filter((c) => c.name !== name));
      toast.success(`Command !${name} deleted`);
    } catch {
      toast.error("Failed to delete command");
    }
  };

  const toggleRule = async (rule: ModRule) => {
    const updated = await api<ModRule>(`/api/moderation/rules/${channel}/${rule.id}`, {
      method: "PUT",
      body: JSON.stringify({ ...rule, enabled: !rule.enabled }),
    });
    setModRules(modRules.map((r) => (r.id === rule.id ? updated : r)));
    toast.success(`Rule "${rule.name}" ${updated.enabled ? "enabled" : "disabled"}`);
  };

  const testModeration = async () => {
    if (!testMessage) return;
    const result = await api<ModerationResult>("/api/moderation/analyze", {
      method: "POST",
      body: JSON.stringify({ username: user?.name || "viewer", message: testMessage, channel }),
    });
    setModResult(result);
  };

  const addTimedMessage = async () => {
    if (!newTimed.message) return;
    try {
      const result = await api<TimedMsg>(`/api/bot/timed/${channel}`, {
        method: "POST",
        body: JSON.stringify({ ...newTimed, enabled: true }),
      });
      setTimedMessages([...timedMessages, result]);
      setNewTimed({ message: "", interval_minutes: 15 });
      setShowAddTimed(false);
      toast.success("Timed message added");
    } catch {
      toast.error("Failed to add timed message");
    }
  };

  const toggleTimedMessage = async (msg: TimedMsg) => {
    try {
      const updated = await api<TimedMsg>(`/api/bot/timed/${channel}/${msg.id}`, {
        method: "PUT",
        body: JSON.stringify({ enabled: !msg.enabled }),
      });
      setTimedMessages(timedMessages.map((m) => (m.id === msg.id ? updated : m)));
      toast.success(`Timed message ${updated.enabled ? "enabled" : "disabled"}`);
    } catch {
      toast.error("Failed to update timed message");
    }
  };

  const deleteTimedMessage = async (id: string) => {
    try {
      await api(`/api/bot/timed/${channel}/${id}`, { method: "DELETE" });
      setTimedMessages(timedMessages.filter((m) => m.id !== id));
      toast.success("Timed message deleted");
    } catch {
      toast.error("Failed to delete timed message");
    }
  };

  const saveWelcomeConfig = async () => {
    if (!botConfig) return;
    try {
      await api("/api/bot/config", {
        method: "POST",
        body: JSON.stringify(botConfig),
      });
      toast.success("Config saved");
    } catch {
      toast.error("Failed to save config");
    }
  };

  const doShoutout = async () => {
    if (!shoutoutTarget) return;
    try {
      const result = await api<ShoutoutResultData>(`/api/bot/shoutout/${channel}`, {
        method: "POST",
        body: JSON.stringify({ target_username: shoutoutTarget }),
      });
      setShoutoutResult(result);
      toast.success(`Shoutout generated for ${result.target_username}`);
    } catch {
      toast.error("Failed to generate shoutout");
    }
  };

  const previewCommand = async () => {
    if (!previewCmd) return;
    try {
      const result = await api<{ resolved_response: string }>(`/api/bot/commands/${channel}/execute`, {
        method: "POST",
        body: JSON.stringify({ command_name: previewCmd, username: user?.name || "viewer" }),
      });
      setPreviewResult(result.resolved_response);
    } catch {
      toast.error("Failed to preview command");
    }
  };

  const insertVariable = (varName: string) => {
    setNewCmd({ ...newCmd, response: newCmd.response + varName });
  };

  const severityColor = (s: number) => {
    if (s >= 3) return "text-red-400 bg-red-500/10";
    if (s >= 2) return "text-amber-400 bg-amber-500/10";
    return "text-blue-400 bg-blue-500/10";
  };

  const actionColor = (a: string) => {
    if (a === "ban") return "text-red-400";
    if (a === "timeout") return "text-orange-400";
    if (a === "delete") return "text-amber-400";
    return "text-blue-400";
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
      <Tabs defaultValue="commands" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="commands" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Bot className="w-4 h-4 mr-2" />
            Commands
          </TabsTrigger>
          <TabsTrigger value="timed" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Clock className="w-4 h-4 mr-2" />
            Timed Messages
          </TabsTrigger>
          <TabsTrigger value="welcome" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <UserCheck className="w-4 h-4 mr-2" />
            Welcome
          </TabsTrigger>
          <TabsTrigger value="shoutout" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Megaphone className="w-4 h-4 mr-2" />
            Shoutout
          </TabsTrigger>
          <TabsTrigger value="moderation" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Shield className="w-4 h-4 mr-2" />
            AI Moderation
          </TabsTrigger>
          <TabsTrigger value="test" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <MessageSquare className="w-4 h-4 mr-2" />
            Test
          </TabsTrigger>
        </TabsList>

        {/* Commands Tab */}
        <TabsContent value="commands" className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">Chat Commands</h3>
              <p className="text-sm text-zinc-500">{commands.length} commands configured</p>
            </div>
            <Button
              onClick={() => setShowAddCmd(!showAddCmd)}
              className="bg-emerald-500 hover:bg-emerald-600 text-black"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Command
            </Button>
          </div>

          {showAddCmd && (
            <Card className="bg-zinc-900/50 border-emerald-500/20">
              <CardContent className="p-4 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-zinc-400 text-xs">Command Name</Label>
                    <div className="flex items-center gap-1">
                      <span className="text-zinc-500">!</span>
                      <Input
                        value={newCmd.name}
                        onChange={(e) => setNewCmd({ ...newCmd, name: e.target.value })}
                        placeholder="command"
                        className="bg-zinc-800 border-zinc-700 text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">Cooldown (seconds)</Label>
                    <Input
                      type="number"
                      value={newCmd.cooldown}
                      onChange={(e) => setNewCmd({ ...newCmd, cooldown: parseInt(e.target.value) })}
                      className="bg-zinc-800 border-zinc-700 text-white"
                    />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <Label className="text-zinc-400 text-xs">Response</Label>
                    <div className="flex items-center gap-1">
                      <Variable className="w-3 h-3 text-zinc-500" />
                      <span className="text-[10px] text-zinc-500">Insert variable:</span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {commandVars.map((v) => (
                      <button
                        key={v.name}
                        onClick={() => insertVariable(v.name)}
                        className="text-[10px] px-2 py-1 rounded bg-zinc-800 text-emerald-400 hover:bg-zinc-700 transition-colors border border-zinc-700"
                        title={v.description}
                      >
                        {v.name}
                      </button>
                    ))}
                  </div>
                  <Textarea
                    value={newCmd.response}
                    onChange={(e) => setNewCmd({ ...newCmd, response: e.target.value })}
                    placeholder="Bot response... Use variables like &#123;username&#125;, &#123;game&#125;, &#123;uptime&#125;"
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={newCmd.mod_only}
                      onCheckedChange={(v) => setNewCmd({ ...newCmd, mod_only: v })}
                    />
                    <Label className="text-zinc-400 text-xs">Mod Only</Label>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" onClick={() => setShowAddCmd(false)} className="text-zinc-400">
                      Cancel
                    </Button>
                    <Button onClick={addCommand} className="bg-emerald-500 hover:bg-emerald-600 text-black">
                      Save Command
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Command Preview */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-emerald-400" />
                <span className="text-sm font-medium text-white">Preview Command</span>
              </div>
              <div className="flex gap-2">
                <select
                  value={previewCmd}
                  onChange={(e) => setPreviewCmd(e.target.value)}
                  className="flex-1 bg-zinc-800 border border-zinc-700 text-white rounded-md px-3 py-2 text-sm"
                >
                  <option value="">Select a command...</option>
                  {commands.map((c) => (
                    <option key={c.name} value={c.name}>!{c.name}</option>
                  ))}
                </select>
                <Button onClick={previewCommand} className="bg-emerald-500 hover:bg-emerald-600 text-black" disabled={!previewCmd}>
                  <Eye className="w-4 h-4 mr-2" />
                  Preview
                </Button>
              </div>
              {previewResult && (
                <div className="p-3 bg-zinc-800 rounded-lg border border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-1">Resolved output:</p>
                  <p className="text-sm text-emerald-400">{previewResult}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="space-y-2">
            {commands.map((cmd) => (
              <Card key={cmd.name} className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <code className="text-emerald-400 font-mono text-sm">!{cmd.name}</code>
                      {cmd.mod_only && (
                        <Badge variant="outline" className="text-[10px] border-amber-500/30 text-amber-400">
                          <Lock className="w-3 h-3 mr-1" />
                          Mod
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-[10px] border-zinc-700 text-zinc-500">
                        {cmd.cooldown}s cooldown
                      </Badge>
                    </div>
                    <p className="text-sm text-zinc-400 mt-1">{cmd.response}</p>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <Button variant="ghost" size="icon" className="text-zinc-500 hover:text-red-400" onClick={() => deleteCommand(cmd.name)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Supported Variables Reference */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                <Variable className="w-4 h-4" />
                Supported Variables
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="grid grid-cols-2 gap-2">
                {commandVars.map((v) => (
                  <div key={v.name} className="flex items-start gap-2 p-2 rounded bg-zinc-800/50">
                    <code className="text-emerald-400 text-xs font-mono whitespace-nowrap">{v.name}</code>
                    <span className="text-xs text-zinc-500">{v.description}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Timed Messages Tab */}
        <TabsContent value="timed" className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">Timed Messages</h3>
              <p className="text-sm text-zinc-500">Auto-post messages at set intervals</p>
            </div>
            <Button
              onClick={() => setShowAddTimed(!showAddTimed)}
              className="bg-emerald-500 hover:bg-emerald-600 text-black"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Timed Message
            </Button>
          </div>

          {showAddTimed && (
            <Card className="bg-zinc-900/50 border-emerald-500/20">
              <CardContent className="p-4 space-y-3">
                <div>
                  <Label className="text-zinc-400 text-xs">Message</Label>
                  <Textarea
                    value={newTimed.message}
                    onChange={(e) => setNewTimed({ ...newTimed, message: e.target.value })}
                    placeholder="Message to auto-post in chat..."
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Interval (minutes)</Label>
                  <Input
                    type="number"
                    min={1}
                    value={newTimed.interval_minutes}
                    onChange={(e) => setNewTimed({ ...newTimed, interval_minutes: parseInt(e.target.value) || 15 })}
                    className="bg-zinc-800 border-zinc-700 text-white w-32"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" onClick={() => setShowAddTimed(false)} className="text-zinc-400">
                    Cancel
                  </Button>
                  <Button onClick={addTimedMessage} className="bg-emerald-500 hover:bg-emerald-600 text-black">
                    Save
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="space-y-2">
            {timedMessages.length === 0 && (
              <div className="text-center py-8 text-zinc-500">
                <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No timed messages configured yet.</p>
              </div>
            )}
            {timedMessages.map((msg) => (
              <Card key={msg.id} className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Switch checked={msg.enabled} onCheckedChange={() => toggleTimedMessage(msg)} />
                    <div className="flex-1">
                      <p className="text-sm text-white">{msg.message}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-[10px] border-zinc-700 text-zinc-500">
                          <Clock className="w-3 h-3 mr-1" />
                          Every {msg.interval_minutes} min
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" className="text-zinc-500 hover:text-red-400" onClick={() => deleteTimedMessage(msg.id)}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Welcome Messages Tab */}
        <TabsContent value="welcome" className="space-y-4 mt-4">
          <div>
            <h3 className="text-lg font-semibold text-white">Welcome Messages</h3>
            <p className="text-sm text-zinc-500">Greet new, returning, and subscriber viewers</p>
          </div>

          {botConfig && (
            <div className="space-y-4">
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <UserCheck className="w-5 h-5 text-emerald-400" />
                      <span className="text-white font-medium">Enable Welcome Messages</span>
                    </div>
                    <Switch
                      checked={botConfig.welcome_enabled}
                      onCheckedChange={(v) => setBotConfig({ ...botConfig, welcome_enabled: v })}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-blue-400">New Viewers</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <Textarea
                    value={botConfig.welcome_new_message || ""}
                    onChange={(e) => setBotConfig({ ...botConfig, welcome_new_message: e.target.value })}
                    placeholder="Welcome to the stream, &#123;username&#125;!"
                    className="bg-zinc-800 border-zinc-700 text-white"
                    disabled={!botConfig.welcome_enabled}
                  />
                  <p className="text-xs text-zinc-600 mt-1">{"Use {username} for the viewer's name"}</p>
                </CardContent>
              </Card>

              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-emerald-400">Returning Viewers</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <Textarea
                    value={botConfig.welcome_returning_message || ""}
                    onChange={(e) => setBotConfig({ ...botConfig, welcome_returning_message: e.target.value })}
                    placeholder="Welcome back, &#123;username&#125;!"
                    className="bg-zinc-800 border-zinc-700 text-white"
                    disabled={!botConfig.welcome_enabled}
                  />
                  <p className="text-xs text-zinc-600 mt-1">{"Use {username} for the viewer's name"}</p>
                </CardContent>
              </Card>

              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-amber-400">Subscriber Viewers</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <Textarea
                    value={botConfig.welcome_subscriber_message || ""}
                    onChange={(e) => setBotConfig({ ...botConfig, welcome_subscriber_message: e.target.value })}
                    placeholder="Thanks for subscribing, &#123;username&#125;!"
                    className="bg-zinc-800 border-zinc-700 text-white"
                    disabled={!botConfig.welcome_enabled}
                  />
                  <p className="text-xs text-zinc-600 mt-1">{"Use {username} for the viewer's name"}</p>
                </CardContent>
              </Card>

              <div className="flex justify-end">
                <Button onClick={saveWelcomeConfig} className="bg-emerald-500 hover:bg-emerald-600 text-black">
                  Save Welcome Messages
                </Button>
              </div>
            </div>
          )}
        </TabsContent>

        {/* Shoutout Tab */}
        <TabsContent value="shoutout" className="space-y-4 mt-4">
          <div>
            <h3 className="text-lg font-semibold text-white">Shoutout Command</h3>
            <p className="text-sm text-zinc-500">Send shoutouts to other streamers</p>
          </div>

          {botConfig && (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-zinc-400">Shoutout Template</CardTitle>
              </CardHeader>
              <CardContent className="pt-0 space-y-3">
                <Textarea
                  value={botConfig.shoutout_template}
                  onChange={(e) => setBotConfig({ ...botConfig, shoutout_template: e.target.value })}
                  placeholder="Check out &#123;target&#125; at kick.com/&#123;target&#125;!"
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
                <p className="text-xs text-zinc-600">
                  {"Variables: {target}, {game}, {title}, {followers}"}
                </p>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={botConfig.auto_shoutout_raiders}
                    onCheckedChange={(v) => setBotConfig({ ...botConfig, auto_shoutout_raiders: v })}
                  />
                  <Label className="text-zinc-400 text-xs">Auto-shoutout raiders</Label>
                </div>
                <div className="flex justify-end">
                  <Button onClick={saveWelcomeConfig} className="bg-emerald-500 hover:bg-emerald-600 text-black">
                    Save Template
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Megaphone className="w-5 h-5 text-emerald-400" />
                Test Shoutout
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={shoutoutTarget}
                  onChange={(e) => setShoutoutTarget(e.target.value)}
                  placeholder="Enter a Kick username..."
                  className="bg-zinc-800 border-zinc-700 text-white"
                  onKeyDown={(e) => e.key === "Enter" && doShoutout()}
                />
                <Button onClick={doShoutout} className="bg-emerald-500 hover:bg-emerald-600 text-black" disabled={!shoutoutTarget}>
                  <Megaphone className="w-4 h-4 mr-2" />
                  Shoutout
                </Button>
              </div>

              {shoutoutResult && (
                <div className="p-4 rounded-lg border border-zinc-700 bg-zinc-800/50 space-y-3">
                  <div className="flex items-center gap-3">
                    {shoutoutResult.avatar_url && (
                      <img src={shoutoutResult.avatar_url} alt="" className="w-10 h-10 rounded-full" />
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-white font-semibold">{shoutoutResult.target_username}</span>
                        {shoutoutResult.is_live && (
                          <Badge className="text-[10px] bg-red-500/20 text-red-400">LIVE</Badge>
                        )}
                      </div>
                      <p className="text-xs text-zinc-500">
                        {shoutoutResult.follower_count.toLocaleString()} followers
                        {shoutoutResult.game && ` | ${shoutoutResult.game}`}
                      </p>
                    </div>
                  </div>
                  <div className="p-3 bg-zinc-900 rounded border border-zinc-700">
                    <p className="text-sm text-emerald-400">{shoutoutResult.message}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Moderation Tab */}
        <TabsContent value="moderation" className="space-y-4 mt-4">
          <div>
            <h3 className="text-lg font-semibold text-white">AI Moderation Rules</h3>
            <p className="text-sm text-zinc-500">Automated chat moderation powered by AI</p>
          </div>

          <div className="space-y-2">
            {modRules.map((rule) => (
              <Card key={rule.id} className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Switch checked={rule.enabled} onCheckedChange={() => toggleRule(rule)} />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-white font-medium">{rule.name}</span>
                        <Badge className={`text-[10px] ${severityColor(rule.severity)}`}>
                          Severity {rule.severity}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-zinc-500">Type: {rule.type}</span>
                        <span className="text-zinc-700">|</span>
                        <span className={`text-xs ${actionColor(rule.action)}`}>
                          Action: {rule.action}
                        </span>
                      </div>
                    </div>
                  </div>
                  <Badge variant="outline" className={`${rule.enabled ? "border-emerald-500/30 text-emerald-400" : "border-zinc-700 text-zinc-500"}`}>
                    {rule.enabled ? "Active" : "Disabled"}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Test Tab */}
        <TabsContent value="test" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-emerald-400" />
                Test AI Moderation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-zinc-500">
                Type a message below to test how the AI moderation would handle it.
              </p>
              <div className="flex gap-2">
                <Input
                  value={testMessage}
                  onChange={(e) => setTestMessage(e.target.value)}
                  placeholder="Type a test chat message..."
                  className="bg-zinc-800 border-zinc-700 text-white"
                  onKeyDown={(e) => e.key === "Enter" && testModeration()}
                />
                <Button onClick={testModeration} className="bg-emerald-500 hover:bg-emerald-600 text-black">
                  <Send className="w-4 h-4 mr-2" />
                  Test
                </Button>
              </div>

              {modResult && (
                <div className={`p-4 rounded-lg border ${modResult.flagged ? "bg-red-500/10 border-red-500/20" : "bg-emerald-500/10 border-emerald-500/20"}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {modResult.flagged ? (
                      <AlertTriangle className="w-5 h-5 text-red-400" />
                    ) : (
                      <Shield className="w-5 h-5 text-emerald-400" />
                    )}
                    <span className={`font-semibold ${modResult.flagged ? "text-red-400" : "text-emerald-400"}`}>
                      {modResult.flagged ? "FLAGGED" : "CLEAN"}
                    </span>
                  </div>
                  {modResult.flagged && (
                    <div className="space-y-1 text-sm">
                      <p className="text-zinc-300">
                        <span className="text-zinc-500">Reason:</span> {modResult.reason}
                      </p>
                      <p className="text-zinc-300">
                        <span className="text-zinc-500">Action:</span>{" "}
                        <span className={actionColor(modResult.action || "")}>{modResult.action}</span>
                      </p>
                      <p className="text-zinc-300">
                        <span className="text-zinc-500">Confidence:</span> {(modResult.confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                  )}
                </div>
              )}

              <Separator className="bg-zinc-800" />

              <div>
                <h4 className="text-sm font-medium text-zinc-400 mb-2">Try these examples:</h4>
                <div className="flex flex-wrap gap-2">
                  {[
                    "This gameplay is garbage, get good noob",
                    "FREE VIEWERS AT bit.ly/scam123",
                    "LETS GOOOOOO THAT WAS INSANE PLAY HOLY MOLY",
                    "Great stream today! Love the content",
                    "aaaaaaaaaaaaaaaa spam spam spam",
                  ].map((example) => (
                    <button
                      key={example}
                      onClick={() => {
                        setTestMessage(example);
                      }}
                      className="text-xs px-3 py-1.5 rounded-full bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white transition-colors"
                    >
                      {example.length > 40 ? example.slice(0, 40) + "..." : example}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
