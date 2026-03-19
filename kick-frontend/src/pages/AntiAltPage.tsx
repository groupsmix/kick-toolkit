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
  ShieldAlert,
  Search,
  UserX,
  UserCheck,
  AlertTriangle,
  Shield,
  Clock,
  Users,
  Eye,
  Crown,
} from "lucide-react";

interface FlaggedAccount {
  username: string;
  risk_score: number;
  risk_level: string;
  flags: string[];
  account_age_days: number;
  follower_count: number;
  is_following: boolean;
  similar_names: string[];
}

interface AntiAltSettings {
  enabled: boolean;
  min_account_age_days: number;
  auto_ban_threshold: number;
  auto_timeout_threshold: number;
  check_name_similarity: boolean;
  check_follow_status: boolean;
  whitelisted_users: string[];
}

const CHANNEL = "demo_streamer";

export function AntiAltPage() {
  const [flagged, setFlagged] = useState<FlaggedAccount[]>([]);
  const [settings, setSettings] = useState<AntiAltSettings | null>(null);
  const [checkUsername, setCheckUsername] = useState("");
  const [checkResult, setCheckResult] = useState<FlaggedAccount | null>(null);
  const [checking, setChecking] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<FlaggedAccount[]>("/api/antialt/flagged").then(setFlagged),
      api<AntiAltSettings>("/api/antialt/settings").then(setSettings),
    ])
      .catch((err) => {
        setError(err.message || "Failed to load anti-alt data");
        toast.error("Failed to load anti-alt data");
      })
      .finally(() => setLoading(false));
  }, []);

  const checkUser = async () => {
    if (!checkUsername) return;
    setChecking(true);
    const result = await api<FlaggedAccount>("/api/antialt/check", {
      method: "POST",
      body: JSON.stringify({ username: checkUsername, channel: CHANNEL }),
    });
    setCheckResult(result);
    setChecking(false);
    // Refresh flagged list
    api<FlaggedAccount[]>("/api/antialt/flagged").then(setFlagged);
  };

  const removeUser = async (username: string) => {
    try {
      await api(`/api/antialt/flagged/${username}`, { method: "DELETE" });
      setFlagged(flagged.filter((a) => a.username !== username));
      toast.success(`${username} removed from flagged list`);
    } catch {
      toast.error("Failed to remove user");
    }
  };

  const whitelistUser = async (username: string) => {
    try {
      await api(`/api/antialt/whitelist/${username}`, { method: "POST" });
      setFlagged(flagged.filter((a) => a.username !== username));
      toast.success(`${username} whitelisted`);
    } catch {
      toast.error("Failed to whitelist user");
    }
  };

  const updateSettings = async (updates: Partial<AntiAltSettings>) => {
    if (!settings) return;
    const newSettings = { ...settings, ...updates };
    const result = await api<AntiAltSettings>("/api/antialt/settings", {
      method: "PUT",
      body: JSON.stringify(newSettings),
    });
    setSettings(result);
  };

  const riskColor = (level: string) => {
    if (level === "critical") return { text: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20", progress: "bg-red-500" };
    if (level === "high") return { text: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/20", progress: "bg-orange-500" };
    if (level === "medium") return { text: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20", progress: "bg-amber-500" };
    return { text: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20", progress: "bg-emerald-500" };
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
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-amber-500/20 via-amber-500/10 to-transparent border border-amber-500/20 p-4">
        <div className="flex items-center gap-3">
          <Crown className="w-6 h-6 text-amber-400" />
          <div>
            <h3 className="text-white font-semibold">Premium Feature: Anti-Alt Detection</h3>
            <p className="text-sm text-zinc-400">AI-powered alt account detection to protect your community</p>
          </div>
          <Badge className="ml-auto bg-amber-500/20 text-amber-400 border-amber-500/30">PRO</Badge>
        </div>
      </div>

      {/* Manual Check */}
      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Search className="w-5 h-5 text-emerald-400" />
            Check Username
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={checkUsername}
              onChange={(e) => setCheckUsername(e.target.value)}
              placeholder="Enter username to check..."
              className="bg-zinc-800 border-zinc-700 text-white"
              onKeyDown={(e) => e.key === "Enter" && checkUser()}
            />
            <Button
              onClick={checkUser}
              disabled={checking}
              className="bg-emerald-500 hover:bg-emerald-600 text-black"
            >
              {checking ? (
                <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Eye className="w-4 h-4 mr-2" />
                  Scan
                </>
              )}
            </Button>
          </div>

          {checkResult && (
            <div className={`p-4 rounded-lg border ${riskColor(checkResult.risk_level).bg} ${riskColor(checkResult.risk_level).border}`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="text-white font-semibold">{checkResult.username}</h4>
                  <Badge className={`mt-1 ${riskColor(checkResult.risk_level).bg} ${riskColor(checkResult.risk_level).text}`}>
                    {checkResult.risk_level.toUpperCase()} RISK
                  </Badge>
                </div>
                <div className="text-right">
                  <p className={`text-3xl font-bold ${riskColor(checkResult.risk_level).text}`}>
                    {checkResult.risk_score.toFixed(0)}
                  </p>
                  <p className="text-xs text-zinc-500">Risk Score</p>
                </div>
              </div>

              <div className="w-full bg-zinc-800 rounded-full h-2 mb-3">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${riskColor(checkResult.risk_level).progress}`}
                  style={{ width: `${checkResult.risk_score}%` }}
                />
              </div>

              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="text-center p-2 rounded bg-zinc-800/50">
                  <p className="text-xs text-zinc-500">Account Age</p>
                  <p className="text-sm text-white font-medium">{checkResult.account_age_days} days</p>
                </div>
                <div className="text-center p-2 rounded bg-zinc-800/50">
                  <p className="text-xs text-zinc-500">Followers</p>
                  <p className="text-sm text-white font-medium">{checkResult.follower_count}</p>
                </div>
                <div className="text-center p-2 rounded bg-zinc-800/50">
                  <p className="text-xs text-zinc-500">Following</p>
                  <p className="text-sm text-white font-medium">{checkResult.is_following ? "Yes" : "No"}</p>
                </div>
              </div>

              {checkResult.flags.length > 0 && (
                <div>
                  <p className="text-xs text-zinc-500 mb-1">Flags:</p>
                  <div className="flex flex-wrap gap-1">
                    {checkResult.flags.map((flag) => (
                      <Badge key={flag} variant="outline" className="text-[10px] border-zinc-700 text-zinc-300">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        {flag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {checkResult.similar_names.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs text-zinc-500 mb-1">Similar to banned users:</p>
                  <div className="flex flex-wrap gap-1">
                    {checkResult.similar_names.map((name) => (
                      <Badge key={name} className="text-[10px] bg-red-500/10 text-red-400">
                        {name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Flagged Accounts */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-red-400" />
            Flagged Accounts ({flagged.length})
          </h3>

          {flagged.map((account) => {
            const colors = riskColor(account.risk_level);
            return (
              <Card key={account.username} className={`bg-zinc-900/50 border-zinc-800 border-l-2 ${colors.border}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-white font-medium">{account.username}</span>
                        <Badge className={`text-[10px] ${colors.bg} ${colors.text}`}>
                          {account.risk_level}
                        </Badge>
                        <span className={`text-sm font-bold ${colors.text}`}>
                          {account.risk_score.toFixed(0)}%
                        </span>
                      </div>

                      <div className="flex items-center gap-3 mt-2 text-xs text-zinc-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {account.account_age_days}d old
                        </span>
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {account.follower_count} followers
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-1 mt-2">
                        {account.flags.map((flag) => (
                          <Badge key={flag} variant="outline" className="text-[10px] border-zinc-700 text-zinc-400">
                            {flag}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="flex gap-1 ml-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => whitelistUser(account.username)}
                        className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                      >
                        <UserCheck className="w-4 h-4 mr-1" />
                        Whitelist
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeUser(account.username)}
                        className="text-zinc-400 hover:text-red-400"
                      >
                        <UserX className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Settings */}
        <div>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-400" />
                Detection Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {settings && (
                <>
                  <div className="flex items-center justify-between">
                    <Label className="text-zinc-300 text-sm">Enabled</Label>
                    <Switch
                      checked={settings.enabled}
                      onCheckedChange={(v) => updateSettings({ enabled: v })}
                    />
                  </div>
                  <Separator className="bg-zinc-800" />
                  <div>
                    <Label className="text-zinc-400 text-xs">Min Account Age (days)</Label>
                    <Input
                      type="number"
                      value={settings.min_account_age_days}
                      onChange={(e) => updateSettings({ min_account_age_days: parseInt(e.target.value) })}
                      className="bg-zinc-800 border-zinc-700 text-white mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">Auto-Ban Threshold</Label>
                    <Input
                      type="number"
                      value={settings.auto_ban_threshold}
                      onChange={(e) => updateSettings({ auto_ban_threshold: parseFloat(e.target.value) })}
                      className="bg-zinc-800 border-zinc-700 text-white mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">Auto-Timeout Threshold</Label>
                    <Input
                      type="number"
                      value={settings.auto_timeout_threshold}
                      onChange={(e) => updateSettings({ auto_timeout_threshold: parseFloat(e.target.value) })}
                      className="bg-zinc-800 border-zinc-700 text-white mt-1"
                    />
                  </div>
                  <Separator className="bg-zinc-800" />
                  <div className="flex items-center justify-between">
                    <Label className="text-zinc-300 text-sm">Name Similarity</Label>
                    <Switch
                      checked={settings.check_name_similarity}
                      onCheckedChange={(v) => updateSettings({ check_name_similarity: v })}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-zinc-300 text-sm">Follow Status</Label>
                    <Switch
                      checked={settings.check_follow_status}
                      onCheckedChange={(v) => updateSettings({ check_follow_status: v })}
                    />
                  </div>

                  {settings.whitelisted_users.length > 0 && (
                    <>
                      <Separator className="bg-zinc-800" />
                      <div>
                        <Label className="text-zinc-400 text-xs">Whitelisted Users</Label>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {settings.whitelisted_users.map((u) => (
                            <Badge key={u} variant="outline" className="border-emerald-500/30 text-emerald-400">
                              <UserCheck className="w-3 h-3 mr-1" />
                              {u}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
