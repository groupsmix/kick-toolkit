import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  Shield,
  Siren,
  Users,
  AlertTriangle,
  CheckCircle,
  Crown,
  Gift,
  Eye,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface RaidEvent {
  id: number | null;
  channel: string;
  detected_at: string | null;
  severity: string;
  new_chatters_count: number;
  window_seconds: number;
  suspicious_accounts: string[];
  auto_action_taken: string;
  resolved: boolean;
  resolved_at: string | null;
}

interface RaidSettings {
  enabled: boolean;
  new_chatter_threshold: number;
  window_seconds: number;
  auto_action: string;
  min_account_age_days: number;
}

interface FraudFlag {
  id: number | null;
  giveaway_id: string;
  username: string;
  flag_type: string;
  matched_username: string | null;
  confidence: number;
  reviewed: boolean;
  review_action: string | null;
  created_at: string | null;
}

export function AntiCheatPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [raids, setRaids] = useState<RaidEvent[]>([]);
  const [raidSettings, setRaidSettings] = useState<RaidSettings | null>(null);
  const [fraudGiveawayId, setFraudGiveawayId] = useState("");
  const [fraudFlags, setFraudFlags] = useState<FraudFlag[]>([]);
  const [activeTab, setActiveTab] = useState<"raids" | "fraud">("raids");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<RaidEvent[]>(`/api/anticheat/raids?channel=${channel}`).then(setRaids),
      api<RaidSettings>("/api/anticheat/raid-settings").then(setRaidSettings),
    ])
      .catch((err) => {
        setError(err.message || "Failed to load anti-cheat data");
        toast.error("Failed to load anti-cheat data");
      })
      .finally(() => setLoading(false));
  }, [channel]);

  const resolveRaid = async (raidId: number) => {
    try {
      await api(`/api/anticheat/raids/${raidId}/resolve`, { method: "POST" });
      setRaids(raids.map((r) => (r.id === raidId ? { ...r, resolved: true } : r)));
      toast.success("Raid event resolved");
    } catch {
      toast.error("Failed to resolve raid");
    }
  };

  const updateRaidSettings = async (updates: Partial<RaidSettings>) => {
    if (!raidSettings) return;
    const newSettings = { ...raidSettings, ...updates };
    try {
      const result = await api<RaidSettings>("/api/anticheat/raid-settings", {
        method: "PUT",
        body: JSON.stringify(newSettings),
      });
      setRaidSettings(result);
      toast.success("Raid settings updated");
    } catch {
      toast.error("Failed to update settings");
    }
  };

  const lookupFraud = async () => {
    if (!fraudGiveawayId) return;
    try {
      const flags = await api<FraudFlag[]>(`/api/anticheat/giveaway-fraud/${fraudGiveawayId}`);
      setFraudFlags(flags);
    } catch {
      toast.error("Failed to load fraud flags");
    }
  };

  const analyzeFraud = async () => {
    if (!fraudGiveawayId) return;
    try {
      await api(`/api/anticheat/giveaway-fraud/${fraudGiveawayId}/analyze`, { method: "POST" });
      const flags = await api<FraudFlag[]>(`/api/anticheat/giveaway-fraud/${fraudGiveawayId}`);
      setFraudFlags(flags);
      toast.success("Fraud analysis complete");
    } catch {
      toast.error("Failed to analyze giveaway");
    }
  };

  const reviewFlag = async (flagId: number, action: string) => {
    try {
      await api("/api/anticheat/giveaway-fraud/review", {
        method: "POST",
        body: JSON.stringify({ flag_id: flagId, action }),
      });
      setFraudFlags(fraudFlags.map((f) => (f.id === flagId ? { ...f, reviewed: true, review_action: action } : f)));
      toast.success(`Flag ${action === "allow" ? "allowed" : "removed"}`);
    } catch {
      toast.error("Failed to review flag");
    }
  };

  const severityColor = (severity: string) => {
    if (severity === "high") return { text: "text-red-400", bg: "bg-red-500/10" };
    if (severity === "medium") return { text: "text-orange-400", bg: "bg-orange-500/10" };
    return { text: "text-amber-400", bg: "bg-amber-500/10" };
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
      {/* Premium Banner */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-purple-500/20 via-purple-500/10 to-transparent border border-purple-500/20 p-4">
        <div className="flex items-center gap-3">
          <Crown className="w-6 h-6 text-purple-400" />
          <div>
            <h3 className="text-white font-semibold">Premium Feature: Anti-Cheat System</h3>
            <p className="text-sm text-zinc-400">Raid detection, giveaway fraud prevention, and queue integrity</p>
          </div>
          <Badge className="ml-auto bg-purple-500/20 text-purple-400 border-purple-500/30">PRO</Badge>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-zinc-800 pb-2">
        {(["raids", "fraud"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === tab
                ? "bg-zinc-800 text-emerald-400 border-b-2 border-emerald-400"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {tab === "raids" && `Raid Detection (${raids.length})`}
            {tab === "fraud" && "Giveaway Fraud"}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-4">
          {/* Raid Detection Tab */}
          {activeTab === "raids" && (
            <>
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Siren className="w-5 h-5 text-red-400" />
                Raid Events
              </h3>

              {raids.length === 0 && (
                <p className="text-zinc-500 text-sm">No raid events detected yet.</p>
              )}

              {raids.map((raid) => {
                const colors = severityColor(raid.severity);
                return (
                  <Card key={raid.id} className={`bg-zinc-900/50 border-zinc-800 ${raid.resolved ? "opacity-60" : ""}`}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Badge className={`text-[10px] ${colors.bg} ${colors.text}`}>
                              {raid.severity.toUpperCase()}
                            </Badge>
                            <span className="text-white font-medium">
                              {raid.new_chatters_count} new chatters in {raid.window_seconds}s
                            </span>
                            {raid.resolved && (
                              <Badge className="text-[10px] bg-emerald-500/10 text-emerald-400">Resolved</Badge>
                            )}
                          </div>

                          <div className="flex items-center gap-3 mt-2 text-xs text-zinc-500">
                            <span>{raid.detected_at}</span>
                            <span>Action: {raid.auto_action_taken}</span>
                          </div>

                          {raid.suspicious_accounts.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs text-zinc-500 mb-1">Suspicious accounts:</p>
                              <div className="flex flex-wrap gap-1">
                                {raid.suspicious_accounts.slice(0, 10).map((name) => (
                                  <Badge key={name} variant="outline" className="text-[10px] border-zinc-700 text-zinc-400">
                                    {name}
                                  </Badge>
                                ))}
                                {raid.suspicious_accounts.length > 10 && (
                                  <Badge variant="outline" className="text-[10px] border-zinc-700 text-zinc-500">
                                    +{raid.suspicious_accounts.length - 10} more
                                  </Badge>
                                )}
                              </div>
                            </div>
                          )}
                        </div>

                        {!raid.resolved && raid.id && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => resolveRaid(raid.id!)}
                            className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                          >
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Resolve
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </>
          )}

          {/* Giveaway Fraud Tab */}
          {activeTab === "fraud" && (
            <>
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Gift className="w-5 h-5 text-purple-400" />
                Giveaway Fraud Detection
              </h3>

              <div className="flex gap-2">
                <Input
                  value={fraudGiveawayId}
                  onChange={(e) => setFraudGiveawayId(e.target.value)}
                  placeholder="Enter giveaway ID..."
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
                <Button onClick={lookupFraud} className="bg-zinc-700 hover:bg-zinc-600 text-white">
                  <Eye className="w-4 h-4 mr-2" />
                  Lookup
                </Button>
                <Button onClick={analyzeFraud} className="bg-purple-500 hover:bg-purple-600 text-white">
                  <Shield className="w-4 h-4 mr-2" />
                  Analyze
                </Button>
              </div>

              {fraudFlags.length === 0 && fraudGiveawayId && (
                <p className="text-zinc-500 text-sm">No fraud flags found for this giveaway.</p>
              )}

              {fraudFlags.map((flag) => (
                <Card key={flag.id} className={`bg-zinc-900/50 border-zinc-800 ${flag.reviewed ? "opacity-60" : ""}`}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-amber-400" />
                          <span className="text-white font-medium">{flag.username}</span>
                          <Badge className="text-[10px] bg-amber-500/10 text-amber-400">{flag.flag_type}</Badge>
                          <span className="text-xs text-zinc-500">
                            Confidence: {(flag.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        {flag.matched_username && (
                          <p className="text-xs text-zinc-500 mt-1">
                            Matched with: <span className="text-zinc-300">{flag.matched_username}</span>
                          </p>
                        )}
                        {flag.reviewed && (
                          <Badge className="mt-1 text-[10px] bg-emerald-500/10 text-emerald-400">
                            Reviewed: {flag.review_action}
                          </Badge>
                        )}
                      </div>

                      {!flag.reviewed && flag.id && (
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => reviewFlag(flag.id!, "allow")}
                            className="text-emerald-400 hover:text-emerald-300"
                          >
                            Allow
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => reviewFlag(flag.id!, "remove")}
                            className="text-red-400 hover:text-red-300"
                          >
                            Remove
                          </Button>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </>
          )}
        </div>

        {/* Raid Settings Sidebar */}
        <div>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-400" />
                Raid Detection Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {raidSettings && (
                <>
                  <div className="flex items-center justify-between">
                    <Label className="text-zinc-300 text-sm">Enabled</Label>
                    <Switch
                      checked={raidSettings.enabled}
                      onCheckedChange={(v) => updateRaidSettings({ enabled: v })}
                    />
                  </div>
                  <Separator className="bg-zinc-800" />
                  <div>
                    <Label className="text-zinc-400 text-xs">New Chatter Threshold</Label>
                    <Input
                      type="number"
                      value={raidSettings.new_chatter_threshold}
                      onChange={(e) => updateRaidSettings({ new_chatter_threshold: parseInt(e.target.value) })}
                      className="bg-zinc-800 border-zinc-700 text-white mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">Window (seconds)</Label>
                    <Input
                      type="number"
                      value={raidSettings.window_seconds}
                      onChange={(e) => updateRaidSettings({ window_seconds: parseInt(e.target.value) })}
                      className="bg-zinc-800 border-zinc-700 text-white mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">Min Account Age (days)</Label>
                    <Input
                      type="number"
                      value={raidSettings.min_account_age_days}
                      onChange={(e) => updateRaidSettings({ min_account_age_days: parseInt(e.target.value) })}
                      className="bg-zinc-800 border-zinc-700 text-white mt-1"
                    />
                  </div>
                  <Separator className="bg-zinc-800" />
                  <div>
                    <Label className="text-zinc-400 text-xs">Auto Action</Label>
                    <select
                      value={raidSettings.auto_action}
                      onChange={(e) => updateRaidSettings({ auto_action: e.target.value })}
                      className="w-full mt-1 bg-zinc-800 border border-zinc-700 text-white rounded-md px-3 py-2 text-sm"
                    >
                      <option value="none">None</option>
                      <option value="slow_mode">Slow Mode</option>
                      <option value="followers_only">Followers Only</option>
                      <option value="subscribers_only">Subscribers Only</option>
                    </select>
                  </div>

                  <Separator className="bg-zinc-800" />
                  <div className="text-center p-3 rounded bg-zinc-800/50">
                    <p className="text-xs text-zinc-500">Active Monitoring</p>
                    <div className="flex items-center justify-center gap-2 mt-1">
                      <Users className="w-4 h-4 text-emerald-400" />
                      <span className="text-white font-medium">
                        {raidSettings.enabled ? "Protected" : "Disabled"}
                      </span>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
