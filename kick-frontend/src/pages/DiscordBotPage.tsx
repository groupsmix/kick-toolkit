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
  MessageCircle,
  Settings,
  Webhook,
  Bell,
  Radio,
  Users,
  Calendar,
  BarChart3,
  Send,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface DiscordSettings {
  channel: string;
  enabled: boolean;
  guild_id: string;
  webhook_url: string;
  go_live_notifications: boolean;
  go_live_channel_id: string;
  go_live_message: string;
  chat_bridge_enabled: boolean;
  chat_bridge_channel_id: string;
  sub_sync_enabled: boolean;
  sub_sync_role_id: string;
  stats_command_enabled: boolean;
  schedule_command_enabled: boolean;
}

interface WebhookEvent {
  id: string;
  channel: string;
  event_type: string;
  payload: Record<string, unknown>;
  status: string;
  error: string | null;
  created_at: string;
}

const EVENT_TYPE_COLORS: Record<string, string> = {
  go_live: "bg-red-500/20 text-red-400",
  new_follow: "bg-emerald-500/20 text-emerald-400",
  new_sub: "bg-purple-500/20 text-purple-400",
  chat_highlight: "bg-blue-500/20 text-blue-400",
};

export function DiscordBotPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [settings, setSettings] = useState<DiscordSettings>({
    channel: "",
    enabled: false,
    guild_id: "",
    webhook_url: "",
    go_live_notifications: true,
    go_live_channel_id: "",
    go_live_message: "",
    chat_bridge_enabled: false,
    chat_bridge_channel_id: "",
    sub_sync_enabled: false,
    sub_sync_role_id: "",
    stats_command_enabled: true,
    schedule_command_enabled: true,
  });
  const [events, setEvents] = useState<WebhookEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    if (!channel) return;
    setLoading(true);
    Promise.all([
      api<DiscordSettings>(`/api/discord/settings/${channel}`).then(setSettings),
      api<WebhookEvent[]>(`/api/discord/events/${channel}`).then(setEvents),
    ])
      .catch(() => toast.error("Failed to load Discord settings"))
      .finally(() => setLoading(false));
  }, [channel]);

  const saveSettings = async () => {
    setSaving(true);
    try {
      const result = await api<DiscordSettings>(`/api/discord/settings/${channel}`, {
        method: "PUT",
        body: JSON.stringify(settings),
      });
      setSettings(result);
      toast.success("Discord settings saved");
    } catch {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const testWebhook = async () => {
    setTesting(true);
    try {
      const event = await api<WebhookEvent>("/api/discord/test", {
        method: "POST",
        body: JSON.stringify({ channel, event_type: "go_live" }),
      });
      setEvents([event, ...events]);
      toast.success("Test notification sent");
    } catch {
      toast.error("Failed to send test notification. Make sure webhook URL is configured.");
    } finally {
      setTesting(false);
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
            <MessageCircle className="w-6 h-6 text-indigo-400" />
            Discord Bot
          </h2>
          <p className="text-sm text-zinc-500">Connect your Kick stream to Discord for notifications and chat bridging</p>
        </div>
        <Badge className={settings.enabled ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-700/50 text-zinc-400"}>
          {settings.enabled ? "Connected" : "Disconnected"}
        </Badge>
      </div>

      <Tabs defaultValue="settings" className="w-full">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="settings" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </TabsTrigger>
          <TabsTrigger value="events" className="data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
            <Webhook className="w-4 h-4 mr-2" />
            Event Log
          </TabsTrigger>
        </TabsList>

        <TabsContent value="settings" className="space-y-4 mt-4">
          {/* Connection */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Webhook className="w-5 h-5 text-indigo-400" />
                Connection
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-white">Enable Discord Integration</Label>
                  <p className="text-xs text-zinc-500">Toggle the entire Discord bot on/off</p>
                </div>
                <Switch checked={settings.enabled} onCheckedChange={(v) => setSettings({ ...settings, enabled: v })} />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Discord Server (Guild) ID</Label>
                <Input value={settings.guild_id} onChange={(e) => setSettings({ ...settings, guild_id: e.target.value })} placeholder="123456789012345678" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Webhook URL</Label>
                <Input value={settings.webhook_url} onChange={(e) => setSettings({ ...settings, webhook_url: e.target.value })} placeholder="https://discord.com/api/webhooks/..." className="bg-zinc-800 border-zinc-700 text-white" />
                <p className="text-xs text-zinc-500 mt-1">Create a webhook in your Discord server settings &gt; Integrations &gt; Webhooks</p>
              </div>
            </CardContent>
          </Card>

          {/* Go Live Notifications */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Bell className="w-5 h-5 text-red-400" />
                Go Live Notifications
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-white">Enable Go Live Alerts</Label>
                  <p className="text-xs text-zinc-500">Post a message when you start streaming on Kick</p>
                </div>
                <Switch checked={settings.go_live_notifications} onCheckedChange={(v) => setSettings({ ...settings, go_live_notifications: v })} />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Notification Channel ID</Label>
                <Input value={settings.go_live_channel_id} onChange={(e) => setSettings({ ...settings, go_live_channel_id: e.target.value })} placeholder="123456789012345678" className="bg-zinc-800 border-zinc-700 text-white" />
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Custom Message Template</Label>
                <Input value={settings.go_live_message} onChange={(e) => setSettings({ ...settings, go_live_message: e.target.value })} placeholder="{streamer} is live! Playing {game}" className="bg-zinc-800 border-zinc-700 text-white" />
                <p className="text-xs text-zinc-500 mt-1">Variables: {"{streamer}"}, {"{game}"}, {"{url}"}, {"{title}"}</p>
              </div>
            </CardContent>
          </Card>

          {/* Features */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Radio className="w-5 h-5 text-emerald-400" />
                Features
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-white flex items-center gap-2">
                    <MessageCircle className="w-4 h-4 text-zinc-400" /> Chat Bridge
                  </Label>
                  <p className="text-xs text-zinc-500">Mirror chat highlights to a Discord channel</p>
                </div>
                <Switch checked={settings.chat_bridge_enabled} onCheckedChange={(v) => setSettings({ ...settings, chat_bridge_enabled: v })} />
              </div>
              {settings.chat_bridge_enabled && (
                <div className="ml-6">
                  <Label className="text-zinc-400 text-xs">Chat Bridge Channel ID</Label>
                  <Input value={settings.chat_bridge_channel_id} onChange={(e) => setSettings({ ...settings, chat_bridge_channel_id: e.target.value })} placeholder="123456789012345678" className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
              )}

              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-white flex items-center gap-2">
                    <Users className="w-4 h-4 text-zinc-400" /> Sub Role Sync
                  </Label>
                  <p className="text-xs text-zinc-500">Auto-assign a Discord role to Kick subscribers</p>
                </div>
                <Switch checked={settings.sub_sync_enabled} onCheckedChange={(v) => setSettings({ ...settings, sub_sync_enabled: v })} />
              </div>
              {settings.sub_sync_enabled && (
                <div className="ml-6">
                  <Label className="text-zinc-400 text-xs">Subscriber Role ID</Label>
                  <Input value={settings.sub_sync_role_id} onChange={(e) => setSettings({ ...settings, sub_sync_role_id: e.target.value })} placeholder="123456789012345678" className="bg-zinc-800 border-zinc-700 text-white" />
                </div>
              )}

              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-white flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-zinc-400" /> Stats Command
                  </Label>
                  <p className="text-xs text-zinc-500">Enable !stats command in Discord</p>
                </div>
                <Switch checked={settings.stats_command_enabled} onCheckedChange={(v) => setSettings({ ...settings, stats_command_enabled: v })} />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-white flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-zinc-400" /> Schedule Command
                  </Label>
                  <p className="text-xs text-zinc-500">Enable !schedule command in Discord</p>
                </div>
                <Switch checked={settings.schedule_command_enabled} onCheckedChange={(v) => setSettings({ ...settings, schedule_command_enabled: v })} />
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex gap-3">
            <Button onClick={saveSettings} disabled={saving} className="bg-indigo-500 hover:bg-indigo-600 text-white flex-1">
              {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Settings className="w-4 h-4 mr-2" />}
              Save Settings
            </Button>
            <Button onClick={testWebhook} disabled={testing || !settings.webhook_url} variant="outline" className="border-zinc-700 text-zinc-300">
              {testing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
              Test Webhook
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="events" className="space-y-4 mt-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Webhook className="w-5 h-5 text-indigo-400" />
                Recent Webhook Events
              </CardTitle>
            </CardHeader>
            <CardContent>
              {events.length === 0 ? (
                <p className="text-zinc-500 text-center py-8">No webhook events recorded yet.</p>
              ) : (
                <div className="space-y-2">
                  {events.map((event) => (
                    <div key={event.id} className="flex items-center gap-3 p-3 rounded-lg bg-zinc-800/50">
                      {event.status === "sent" ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                      ) : event.status === "failed" ? (
                        <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                      ) : (
                        <Clock className="w-5 h-5 text-amber-400 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Badge className={EVENT_TYPE_COLORS[event.event_type] || "bg-zinc-700/50 text-zinc-400"}>
                            {event.event_type.replace("_", " ")}
                          </Badge>
                          <span className="text-xs text-zinc-500">
                            {new Date(event.created_at).toLocaleString()}
                          </span>
                        </div>
                        {event.error && <p className="text-xs text-red-400 mt-1">{event.error}</p>}
                      </div>
                      <Badge className={
                        event.status === "sent" ? "bg-emerald-500/20 text-emerald-400" :
                        event.status === "failed" ? "bg-red-500/20 text-red-400" :
                        "bg-amber-500/20 text-amber-400"
                      }>
                        {event.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
