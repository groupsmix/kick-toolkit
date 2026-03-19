import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { api } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import {
  MessageCircle,
  Bell,
  Link2,
  Users,
  Calendar,
  BarChart3,
  Save,
  Wifi,
} from "lucide-react";

interface DiscordConfig {
  id?: string;
  channel: string;
  configured?: boolean;
  guild_id: string;
  webhook_url: string;
  go_live_enabled: boolean;
  go_live_channel_id: string;
  go_live_message: string;
  chat_bridge_enabled: boolean;
  chat_bridge_channel_id: string;
  sub_sync_enabled: boolean;
  sub_sync_role_id: string;
  stats_commands_enabled: boolean;
  schedule_display_enabled: boolean;
  schedule_channel_id: string;
}

interface DiscordStatus {
  channel: string;
  connected: boolean;
  guild_name: string;
  features_active: string[];
  last_ping: string | null;
}

const DEFAULT_CONFIG: DiscordConfig = {
  channel: "",
  guild_id: "",
  webhook_url: "",
  go_live_enabled: true,
  go_live_channel_id: "",
  go_live_message: "{streamer} is now live on Kick! Playing {game} - {title}",
  chat_bridge_enabled: false,
  chat_bridge_channel_id: "",
  sub_sync_enabled: false,
  sub_sync_role_id: "",
  stats_commands_enabled: true,
  schedule_display_enabled: true,
  schedule_channel_id: "",
};

export function DiscordBotPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [config, setConfig] = useState<DiscordConfig>({ ...DEFAULT_CONFIG, channel });
  const [status, setStatus] = useState<DiscordStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [configData, statusData] = await Promise.all([
        api<DiscordConfig>(`/api/discord/config/${channel}`),
        api<DiscordStatus>(`/api/discord/status/${channel}`),
      ]);
      if (!configData.configured) {
        setConfig({ ...DEFAULT_CONFIG, channel });
      } else {
        setConfig(configData);
      }
      setStatus(statusData);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load Discord config");
    } finally {
      setLoading(false);
    }
  }, [channel]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  const saveConfig = async () => {
    setSaving(true);
    try {
      await api(`/api/discord/config/${channel}`, {
        method: "PUT",
        body: JSON.stringify({
          guild_id: config.guild_id,
          webhook_url: config.webhook_url,
          go_live_enabled: config.go_live_enabled,
          go_live_channel_id: config.go_live_channel_id,
          go_live_message: config.go_live_message,
          chat_bridge_enabled: config.chat_bridge_enabled,
          chat_bridge_channel_id: config.chat_bridge_channel_id,
          sub_sync_enabled: config.sub_sync_enabled,
          sub_sync_role_id: config.sub_sync_role_id,
          stats_commands_enabled: config.stats_commands_enabled,
          schedule_display_enabled: config.schedule_display_enabled,
          schedule_channel_id: config.schedule_channel_id,
        }),
      });
      toast.success("Discord configuration saved!");
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save config");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-indigo-500/20 via-blue-500/10 to-transparent border border-indigo-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <MessageCircle className="w-6 h-6 text-indigo-400" />
              <h2 className="text-2xl font-bold text-white">Discord Bot</h2>
              <Badge className="bg-indigo-500/20 text-indigo-400 border-indigo-500/30 text-[10px] uppercase font-bold">
                Pro
              </Badge>
            </div>
            <p className="text-zinc-400">
              Connect your Discord server. Go-live notifications, sub sync, stats commands, and more.
            </p>
          </div>
          <Button
            className="bg-indigo-600 hover:bg-indigo-700"
            onClick={saveConfig}
            disabled={saving}
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? "Saving..." : "Save Config"}
          </Button>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <MessageCircle className="w-32 h-32 text-indigo-500" />
        </div>
      </div>

      {/* Connection Status */}
      {status && (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${status.connected ? "bg-emerald-400 animate-pulse" : "bg-zinc-600"}`} />
              <div>
                <p className="text-sm font-medium text-white">
                  {status.connected ? "Connected" : "Not Connected"}
                </p>
                {status.guild_name && (
                  <p className="text-xs text-zinc-500">{status.guild_name}</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {status.features_active.map((f) => (
                <Badge key={f} className="bg-indigo-500/10 text-indigo-400 text-[10px]">
                  {f.replace("_", " ")}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Server Connection */}
      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <Wifi className="w-4 h-4 text-indigo-400" />
            Server Connection
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className="text-xs text-zinc-500">Discord Server (Guild) ID</Label>
              <Input
                className="bg-zinc-800 border-zinc-700 mt-1"
                value={config.guild_id}
                onChange={(e) => setConfig({ ...config, guild_id: e.target.value })}
                placeholder="123456789012345678"
              />
            </div>
            <div>
              <Label className="text-xs text-zinc-500">Webhook URL</Label>
              <Input
                className="bg-zinc-800 border-zinc-700 mt-1"
                value={config.webhook_url}
                onChange={(e) => setConfig({ ...config, webhook_url: e.target.value })}
                placeholder="https://discord.com/api/webhooks/..."
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Go-Live Notifications */}
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <Bell className="w-4 h-4 text-emerald-400" />
                Go-Live Notifications
              </CardTitle>
              <Switch
                checked={config.go_live_enabled}
                onCheckedChange={(v) => setConfig({ ...config, go_live_enabled: v })}
              />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label className="text-xs text-zinc-500">Notification Channel ID</Label>
              <Input
                className="bg-zinc-800 border-zinc-700 mt-1"
                value={config.go_live_channel_id}
                onChange={(e) => setConfig({ ...config, go_live_channel_id: e.target.value })}
                placeholder="Channel ID for notifications"
                disabled={!config.go_live_enabled}
              />
            </div>
            <div>
              <Label className="text-xs text-zinc-500">
                Message Template
                <span className="text-zinc-600 ml-1">(use {"{streamer}"}, {"{game}"}, {"{title}"})</span>
              </Label>
              <Input
                className="bg-zinc-800 border-zinc-700 mt-1"
                value={config.go_live_message}
                onChange={(e) => setConfig({ ...config, go_live_message: e.target.value })}
                disabled={!config.go_live_enabled}
              />
            </div>
          </CardContent>
        </Card>

        {/* Chat Bridge */}
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <Link2 className="w-4 h-4 text-blue-400" />
                Chat Bridge
              </CardTitle>
              <Switch
                checked={config.chat_bridge_enabled}
                onCheckedChange={(v) => setConfig({ ...config, chat_bridge_enabled: v })}
              />
            </div>
          </CardHeader>
          <CardContent>
            <div>
              <Label className="text-xs text-zinc-500">Bridge Channel ID</Label>
              <Input
                className="bg-zinc-800 border-zinc-700 mt-1"
                value={config.chat_bridge_channel_id}
                onChange={(e) => setConfig({ ...config, chat_bridge_channel_id: e.target.value })}
                placeholder="Channel to mirror Kick chat"
                disabled={!config.chat_bridge_enabled}
              />
            </div>
            <p className="text-[10px] text-zinc-600 mt-2">
              Mirror Kick chat highlights to a Discord channel during streams.
            </p>
          </CardContent>
        </Card>

        {/* Sub Sync */}
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <Users className="w-4 h-4 text-violet-400" />
                Subscriber Sync
              </CardTitle>
              <Switch
                checked={config.sub_sync_enabled}
                onCheckedChange={(v) => setConfig({ ...config, sub_sync_enabled: v })}
              />
            </div>
          </CardHeader>
          <CardContent>
            <div>
              <Label className="text-xs text-zinc-500">Subscriber Role ID</Label>
              <Input
                className="bg-zinc-800 border-zinc-700 mt-1"
                value={config.sub_sync_role_id}
                onChange={(e) => setConfig({ ...config, sub_sync_role_id: e.target.value })}
                placeholder="Discord role for Kick subscribers"
                disabled={!config.sub_sync_enabled}
              />
            </div>
            <p className="text-[10px] text-zinc-600 mt-2">
              Automatically assign a Discord role to active Kick subscribers.
            </p>
          </CardContent>
        </Card>

        {/* Stats & Schedule */}
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-amber-400" />
              Stats & Schedule
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-zinc-500" />
                <span className="text-sm text-zinc-300">Stats Commands (!stats, !uptime)</span>
              </div>
              <Switch
                checked={config.stats_commands_enabled}
                onCheckedChange={(v) => setConfig({ ...config, stats_commands_enabled: v })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-zinc-500" />
                <span className="text-sm text-zinc-300">Schedule Display</span>
              </div>
              <Switch
                checked={config.schedule_display_enabled}
                onCheckedChange={(v) => setConfig({ ...config, schedule_display_enabled: v })}
              />
            </div>
            {config.schedule_display_enabled && (
              <div>
                <Label className="text-xs text-zinc-500">Schedule Channel ID</Label>
                <Input
                  className="bg-zinc-800 border-zinc-700 mt-1"
                  value={config.schedule_channel_id}
                  onChange={(e) => setConfig({ ...config, schedule_channel_id: e.target.value })}
                  placeholder="Channel to display schedule"
                />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
