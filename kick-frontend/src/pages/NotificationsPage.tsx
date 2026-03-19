import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import {
  Bell,
  Send,
  Settings,
  History,
  Webhook,
  MessageCircle,
  CheckCircle,
  Plus,
  Trash2,
  RefreshCw,
  Radio,
} from "lucide-react";

interface NotificationSettings {
  channel: string;
  go_live_enabled: boolean;
  webhook_urls: string[];
  discord_webhook_url: string;
  notification_message: string;
  notify_on_title_change: boolean;
  notify_on_game_change: boolean;
  updated_at?: string;
}

interface NotificationLogEntry {
  id: string;
  channel: string;
  notification_type: string;
  message: string;
  targets: string[];
  status: string;
  created_at: string;
}

export function NotificationsPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [settings, setSettings] = useState<NotificationSettings>({
    channel: "",
    go_live_enabled: false,
    webhook_urls: [],
    discord_webhook_url: "",
    notification_message: "{channel} is now live! Playing {game} — {title}",
    notify_on_title_change: false,
    notify_on_game_change: false,
  });
  const [history, setHistory] = useState<NotificationLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);
  const [newWebhook, setNewWebhook] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const [settingsData, historyData] = await Promise.all([
        api<NotificationSettings>(`/api/schedule/${channel}/notifications/settings`),
        api<NotificationLogEntry[]>(`/api/schedule/${channel}/notifications/history`),
      ]);
      setSettings(settingsData);
      setHistory(historyData);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load notifications");
    } finally {
      setLoading(false);
    }
  }, [channel]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  const saveSettings = async () => {
    setSaving(true);
    try {
      const result = await api<NotificationSettings>(
        `/api/schedule/${channel}/notifications/settings`,
        {
          method: "PUT",
          body: JSON.stringify({
            go_live_enabled: settings.go_live_enabled,
            webhook_urls: settings.webhook_urls,
            discord_webhook_url: settings.discord_webhook_url,
            notification_message: settings.notification_message,
            notify_on_title_change: settings.notify_on_title_change,
            notify_on_game_change: settings.notify_on_game_change,
          }),
        }
      );
      setSettings(result);
      toast.success("Notification settings saved!");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const sendNotification = async () => {
    setSending(true);
    try {
      await api(`/api/schedule/${channel}/notify`, { method: "POST" });
      toast.success("Go-live notification sent!");
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to send notification");
    } finally {
      setSending(false);
    }
  };

  const addWebhook = () => {
    if (!newWebhook.trim()) return;
    setSettings({
      ...settings,
      webhook_urls: [...settings.webhook_urls, newWebhook.trim()],
    });
    setNewWebhook("");
  };

  const removeWebhook = (index: number) => {
    setSettings({
      ...settings,
      webhook_urls: settings.webhook_urls.filter((_, i) => i !== index),
    });
  };

  const formatDate = (ts: string) =>
    new Date(ts).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-violet-500/20 via-fuchsia-500/10 to-transparent border border-violet-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Bell className="w-6 h-6 text-violet-400" />
              <h2 className="text-2xl font-bold text-white">Go-Live Notifications</h2>
            </div>
            <p className="text-zinc-400">
              Automatically notify your community when you go live via Discord webhooks and custom endpoints.
            </p>
          </div>
          <Button
            onClick={sendNotification}
            disabled={sending || !settings.go_live_enabled}
            className="bg-violet-500 hover:bg-violet-600 text-white"
          >
            {sending ? (
              <RefreshCw className="w-4 h-4 animate-spin mr-1" />
            ) : (
              <Send className="w-4 h-4 mr-1" />
            )}
            Send Now
          </Button>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <Bell className="w-32 h-32 text-violet-500" />
        </div>
      </div>

      <Tabs defaultValue="settings" className="space-y-4">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="settings" className="data-[state=active]:bg-zinc-800">
            <Settings className="w-4 h-4 mr-1" />
            Settings
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-zinc-800">
            <History className="w-4 h-4 mr-1" />
            History
          </TabsTrigger>
        </TabsList>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          {/* Enable Toggle */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center">
                    <Radio className="w-5 h-5 text-violet-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">Go-Live Notifications</p>
                    <p className="text-xs text-zinc-500">
                      Send notifications when your stream goes live
                    </p>
                  </div>
                </div>
                <Switch
                  checked={settings.go_live_enabled}
                  onCheckedChange={(v) => setSettings({ ...settings, go_live_enabled: v })}
                />
              </div>
            </CardContent>
          </Card>

          {/* Discord Webhook */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <MessageCircle className="w-4 h-4 text-indigo-400" />
                Discord Webhook
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-zinc-400 text-xs">Discord Webhook URL</Label>
                <Input
                  value={settings.discord_webhook_url}
                  onChange={(e) =>
                    setSettings({ ...settings, discord_webhook_url: e.target.value })
                  }
                  placeholder="https://discord.com/api/webhooks/..."
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
                <p className="text-[10px] text-zinc-600 mt-1">
                  Create a webhook in your Discord server settings &gt; Integrations
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Custom Webhooks */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <Webhook className="w-4 h-4 text-cyan-400" />
                Custom Webhook URLs
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {settings.webhook_urls.map((url, i) => (
                <div key={i} className="flex items-center gap-2">
                  <Input
                    value={url}
                    readOnly
                    className="bg-zinc-800 border-zinc-700 text-zinc-300 flex-1"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-zinc-600 hover:text-red-400"
                    onClick={() => removeWebhook(i)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
              <div className="flex items-center gap-2">
                <Input
                  value={newWebhook}
                  onChange={(e) => setNewWebhook(e.target.value)}
                  placeholder="https://your-webhook-endpoint.com/notify"
                  className="bg-zinc-800 border-zinc-700 text-white flex-1"
                  onKeyDown={(e) => e.key === "Enter" && addWebhook()}
                />
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-cyan-400 hover:text-cyan-300"
                  onClick={addWebhook}
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Message Template */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400">Notification Message</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-zinc-400 text-xs">
                  Template (use {"{channel}"}, {"{game}"}, {"{title}"} as placeholders)
                </Label>
                <Input
                  value={settings.notification_message}
                  onChange={(e) =>
                    setSettings({ ...settings, notification_message: e.target.value })
                  }
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <div className="p-3 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
                <p className="text-[10px] text-zinc-500 uppercase mb-1">Preview</p>
                <p className="text-sm text-zinc-300">
                  {settings.notification_message
                    .replace("{channel}", channel || "your_channel")
                    .replace("{game}", "Valorant")
                    .replace("{title}", "Road to Immortal")}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Additional Options */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400">Additional Triggers</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-white">Title Change Notification</p>
                  <p className="text-xs text-zinc-500">
                    Notify when you update the stream title
                  </p>
                </div>
                <Switch
                  checked={settings.notify_on_title_change}
                  onCheckedChange={(v) =>
                    setSettings({ ...settings, notify_on_title_change: v })
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-white">Game Change Notification</p>
                  <p className="text-xs text-zinc-500">
                    Notify when you switch to a different game
                  </p>
                </div>
                <Switch
                  checked={settings.notify_on_game_change}
                  onCheckedChange={(v) =>
                    setSettings({ ...settings, notify_on_game_change: v })
                  }
                />
              </div>
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end">
            <Button
              onClick={saveSettings}
              disabled={saving}
              className="bg-emerald-500 hover:bg-emerald-600 text-black"
            >
              {saving ? (
                <RefreshCw className="w-4 h-4 animate-spin mr-1" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-1" />
              )}
              Save Settings
            </Button>
          </div>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <History className="w-4 h-4 text-violet-400" />
                Notification History
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[500px]">
                <div className="space-y-1 p-4">
                  {history.map((entry) => (
                    <Card key={entry.id} className="bg-zinc-900/30 border-zinc-800/50">
                      <CardContent className="p-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge
                                className={
                                  entry.status === "sent"
                                    ? "bg-emerald-500/10 text-emerald-400 text-[10px]"
                                    : "bg-red-500/10 text-red-400 text-[10px]"
                                }
                              >
                                {entry.status}
                              </Badge>
                              <Badge className="bg-violet-500/10 text-violet-400 text-[10px]">
                                {entry.notification_type.replace("_", " ")}
                              </Badge>
                            </div>
                            <p className="text-sm text-zinc-300 mt-1">{entry.message}</p>
                            <div className="flex items-center gap-2 mt-2 flex-wrap">
                              {entry.targets.map((target, i) => (
                                <span
                                  key={i}
                                  className="text-[10px] text-zinc-500 bg-zinc-800/50 px-2 py-0.5 rounded"
                                >
                                  {target}
                                </span>
                              ))}
                            </div>
                          </div>
                          <span className="text-[11px] text-zinc-600 whitespace-nowrap ml-2">
                            {formatDate(entry.created_at)}
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {history.length === 0 && (
                    <div className="text-center py-8">
                      <Bell className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                      <p className="text-zinc-400 text-sm">No notifications sent yet</p>
                      <p className="text-zinc-600 text-xs mt-1">
                        Configure your settings and send a test notification
                      </p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
