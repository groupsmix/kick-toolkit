import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, useApiUrl } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  Monitor,
  Copy,
  RefreshCw,
  ExternalLink,
  MessageSquare,
  Bell,
  Gift,
  Music,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface OverlayConfig {
  id: string;
  channel: string;
  overlay_type: string;
  enabled: boolean;
  token: string;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

const OVERLAY_META: Record<string, { label: string; description: string; icon: React.ElementType; color: string }> = {
  chat: { label: "Chat Overlay", description: "Show live chat messages on stream", icon: MessageSquare, color: "text-blue-400" },
  alerts: { label: "Alert Box", description: "Display follow/sub/raid alerts on stream", icon: Bell, color: "text-amber-400" },
  giveaway: { label: "Giveaway Widget", description: "Show active giveaway status on stream", icon: Gift, color: "text-pink-400" },
  nowplaying: { label: "Now Playing", description: "Show current song from song requests", icon: Music, color: "text-purple-400" },
};

export function OverlaysPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const apiUrl = useApiUrl();
  const [overlays, setOverlays] = useState<OverlayConfig[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<OverlayConfig[]>(`/api/overlays/${channel}`)
      .then(setOverlays)
      .catch(() => toast.error("Failed to load overlays"))
      .finally(() => setLoading(false));
  }, [channel]);

  const toggleOverlay = async (overlay: OverlayConfig) => {
    try {
      const result = await api<OverlayConfig>(`/api/overlays/${channel}/${overlay.overlay_type}`, {
        method: "PUT",
        body: JSON.stringify({ enabled: !overlay.enabled }),
      });
      setOverlays(overlays.map((o) => (o.overlay_type === overlay.overlay_type ? result : o)));
      toast.success(`${OVERLAY_META[overlay.overlay_type]?.label || overlay.overlay_type} ${result.enabled ? "enabled" : "disabled"}`);
    } catch {
      toast.error("Failed to update overlay");
    }
  };

  const regenerateToken = async (overlayType: string) => {
    try {
      const result = await api<OverlayConfig>(`/api/overlays/${channel}/${overlayType}/regenerate-token`, {
        method: "POST",
      });
      setOverlays(overlays.map((o) => (o.overlay_type === overlayType ? result : o)));
      toast.success("Token regenerated. Update your OBS browser source URL.");
    } catch {
      toast.error("Failed to regenerate token");
    }
  };

  const getOverlayUrl = (token: string) => `${apiUrl}/api/overlays/render/${token}`;

  const copyUrl = (token: string) => {
    navigator.clipboard.writeText(getOverlayUrl(token));
    toast.success("URL copied to clipboard");
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
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Monitor className="w-6 h-6 text-cyan-400" />
          OBS Overlays
        </h2>
        <p className="text-sm text-zinc-500">Add browser sources to OBS for live stream widgets</p>
      </div>

      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10">
              <Monitor className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-white">How to use overlays</h3>
              <ol className="text-xs text-zinc-500 mt-1 space-y-1 list-decimal list-inside">
                <li>Enable the overlay you want to use</li>
                <li>Copy the browser source URL</li>
                <li>In OBS, add a new &quot;Browser&quot; source</li>
                <li>Paste the URL and set the width/height to match your stream</li>
              </ol>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {overlays.map((overlay) => {
          const meta = OVERLAY_META[overlay.overlay_type] || {
            label: overlay.overlay_type,
            description: "",
            icon: Monitor,
            color: "text-zinc-400",
          };
          const Icon = meta.icon;

          return (
            <Card key={overlay.overlay_type} className={`bg-zinc-900/50 border-zinc-800 ${overlay.enabled ? "" : "opacity-60"}`}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Icon className={`w-5 h-5 ${meta.color}`} />
                    <span className="text-white text-base">{meta.label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={overlay.enabled ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-700/50 text-zinc-500"}>
                      {overlay.enabled ? "Active" : "Off"}
                    </Badge>
                    <Switch checked={overlay.enabled} onCheckedChange={() => toggleOverlay(overlay)} />
                  </div>
                </CardTitle>
                <p className="text-xs text-zinc-500">{meta.description}</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <Label className="text-zinc-400 text-xs">Browser Source URL</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Input
                      readOnly
                      value={overlay.token ? getOverlayUrl(overlay.token) : "Enable to generate URL"}
                      className="bg-zinc-800 border-zinc-700 text-zinc-300 text-xs font-mono"
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-zinc-500 hover:text-white shrink-0"
                      onClick={() => copyUrl(overlay.token)}
                      disabled={!overlay.token}
                      title="Copy URL"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-zinc-500 hover:text-amber-400 shrink-0"
                      onClick={() => window.open(getOverlayUrl(overlay.token), "_blank")}
                      disabled={!overlay.token}
                      title="Preview"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-zinc-700 text-zinc-400 hover:text-amber-400 text-xs"
                    onClick={() => regenerateToken(overlay.overlay_type)}
                  >
                    <RefreshCw className="w-3 h-3 mr-1" />
                    Regenerate Token
                  </Button>
                  <span className="text-[10px] text-zinc-600">Token: {overlay.token?.slice(0, 8)}...</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {overlays.length === 0 && (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardContent className="p-8 text-center">
            <Monitor className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
            <p className="text-zinc-500">No overlays configured. They will be created automatically when you first access this page.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
