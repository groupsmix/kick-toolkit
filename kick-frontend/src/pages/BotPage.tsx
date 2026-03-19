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
} from "lucide-react";

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

const CHANNEL = "demo_streamer";

export function BotPage() {
  const [commands, setCommands] = useState<BotCommand[]>([]);
  const [modRules, setModRules] = useState<ModRule[]>([]);
  const [newCmd, setNewCmd] = useState({ name: "", response: "", cooldown: 5, mod_only: false });
  const [testMessage, setTestMessage] = useState("");
  const [modResult, setModResult] = useState<ModerationResult | null>(null);
  const [showAddCmd, setShowAddCmd] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<BotCommand[]>(`/api/bot/commands/${CHANNEL}`).then(setCommands),
      api<ModRule[]>(`/api/moderation/rules/${CHANNEL}`).then(setModRules),
    ])
      .catch((err) => {
        setError(err.message || "Failed to load bot data");
        toast.error("Failed to load bot data");
      })
      .finally(() => setLoading(false));
  }, []);

  const addCommand = async () => {
    if (!newCmd.name || !newCmd.response) return;
    const cmd = await api<BotCommand>(`/api/bot/commands/${CHANNEL}`, {
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
      await api(`/api/bot/commands/${CHANNEL}/${name}`, { method: "DELETE" });
      setCommands(commands.filter((c) => c.name !== name));
      toast.success(`Command !${name} deleted`);
    } catch {
      toast.error("Failed to delete command");
    }
  };

  const toggleRule = async (rule: ModRule) => {
    const updated = await api<ModRule>(`/api/moderation/rules/${CHANNEL}/${rule.id}`, {
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
      body: JSON.stringify({ username: "test_user", message: testMessage, channel: CHANNEL }),
    });
    setModResult(result);
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
                  <Label className="text-zinc-400 text-xs">Response</Label>
                  <Textarea
                    value={newCmd.response}
                    onChange={(e) => setNewCmd({ ...newCmd, response: e.target.value })}
                    placeholder="Bot response message..."
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
