import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/useAuth";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/hooks/useApi";
import type { SubscriptionResponse } from "@/types";
import { useNavigate } from "react-router-dom";
import {
  User,
  Bell,
  Shield,
  CreditCard,
  LogOut,
  Crown,
  ArrowUpRight,
  Globe,
  Clock,
} from "lucide-react";
import { toast } from "sonner";

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const { data: subData } = useQuery<SubscriptionResponse>({
    queryKey: ["subscription"],
    queryFn: () => api<SubscriptionResponse>("/api/subscription/me"),
  });

  const currentPlan = subData?.plan?.name || "Free";
  const planId = subData?.plan?.id || "free";

  // Notification preferences (persisted to localStorage)
  const [notifications, setNotifications] = useState(() => {
    try {
      const saved = localStorage.getItem("kick_notification_prefs");
      if (saved) return JSON.parse(saved);
    } catch { /* ignore parse errors */ }
    return {
      moderation_alerts: true,
      giveaway_complete: true,
      tournament_updates: true,
      weekly_summary: false,
      browser_push: false,
    };
  });

  const updateNotifications = (updated: typeof notifications) => {
    setNotifications(updated);
    localStorage.setItem("kick_notification_prefs", JSON.stringify(updated));
  };

  // Timezone
  const [timezone, setTimezone] = useState(
    Intl.DateTimeFormat().resolvedOptions().timeZone
  );

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Manage your account, notifications, and preferences.
        </p>
      </div>

      {/* Account Section */}
      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <User className="w-4 h-4" />
            Account
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            {user?.profile_picture ? (
              <img
                src={user.profile_picture}
                alt={user.name}
                className="w-16 h-16 rounded-full border-2 border-zinc-700"
              />
            ) : (
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center border-2 border-zinc-700">
                <span className="text-2xl font-bold text-emerald-400">
                  {user?.name?.charAt(0)?.toUpperCase() || "?"}
                </span>
              </div>
            )}
            <div>
              <p className="text-lg font-semibold text-white">{user?.name}</p>
              {user?.email && (
                <p className="text-sm text-zinc-500">{user.email}</p>
              )}
              {user?.streamer_channel && (
                <p className="text-xs text-zinc-600 mt-1">
                  Channel: {user.streamer_channel}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Subscription Section */}
      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <CreditCard className="w-4 h-4" />
            Subscription
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Badge
                className={`px-3 py-1 text-xs font-bold uppercase tracking-wider ${
                  planId === "premium"
                    ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                    : planId === "pro"
                    ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                    : "bg-zinc-700/50 text-zinc-400 border-zinc-600/30"
                }`}
              >
                <Crown className="w-3 h-3 mr-1" />
                {currentPlan}
              </Badge>
              <span className="text-sm text-zinc-400">
                {planId === "free"
                  ? "Limited features"
                  : planId === "pro"
                  ? "$9.99/month"
                  : "$24.99/month"}
              </span>
            </div>
            {planId === "free" && (
              <Button
                size="sm"
                className="bg-emerald-500 hover:bg-emerald-600 text-black text-xs font-semibold"
                onClick={() => navigate("/pricing")}
              >
                Upgrade
                <ArrowUpRight className="w-3 h-3 ml-1" />
              </Button>
            )}
          </div>
          {planId !== "free" && (
            <p className="text-xs text-zinc-600">
              Manage your subscription through LemonSqueezy or contact support
              to cancel.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Notifications Section */}
      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <Bell className="w-4 h-4" />
            Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Moderation Alerts</p>
              <p className="text-xs text-zinc-500">
                Get notified when AI flags a message
              </p>
            </div>
            <Switch
              checked={notifications.moderation_alerts}
              onCheckedChange={(v) =>
                updateNotifications({ ...notifications, moderation_alerts: v })
              }
            />
          </div>
          <Separator className="bg-zinc-800" />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Giveaway Complete</p>
              <p className="text-xs text-zinc-500">
                Notify when a giveaway finishes
              </p>
            </div>
            <Switch
              checked={notifications.giveaway_complete}
              onCheckedChange={(v) =>
                updateNotifications({ ...notifications, giveaway_complete: v })
              }
            />
          </div>
          <Separator className="bg-zinc-800" />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Tournament Updates</p>
              <p className="text-xs text-zinc-500">
                Match results and bracket updates
              </p>
            </div>
            <Switch
              checked={notifications.tournament_updates}
              onCheckedChange={(v) =>
                updateNotifications({ ...notifications, tournament_updates: v })
              }
            />
          </div>
          <Separator className="bg-zinc-800" />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Weekly Summary</p>
              <p className="text-xs text-zinc-500">
                Weekly email with your stream stats
              </p>
            </div>
            <Switch
              checked={notifications.weekly_summary}
              onCheckedChange={(v) =>
                updateNotifications({ ...notifications, weekly_summary: v })
              }
            />
          </div>
          <Separator className="bg-zinc-800" />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Browser Push Notifications</p>
              <p className="text-xs text-zinc-500">
                Receive push notifications in your browser
              </p>
            </div>
            <Switch
              checked={notifications.browser_push}
              onCheckedChange={(v) => {
                updateNotifications({ ...notifications, browser_push: v });
                if (v) {
                  toast.info(
                    "Browser notifications will be available in a future update."
                  );
                }
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Preferences Section */}
      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <Globe className="w-4 h-4" />
            Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-zinc-400 text-xs flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Timezone
            </Label>
            <Input
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="bg-zinc-800 border-zinc-700 text-white mt-1 max-w-sm"
              placeholder="America/New_York"
            />
            <p className="text-xs text-zinc-600 mt-1">
              Used for scheduling and analytics timestamps.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Security Section */}
      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Security
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Connected via Kick OAuth</p>
              <p className="text-xs text-zinc-500">
                Your Kick account is connected securely via OAuth 2.1
              </p>
            </div>
            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/20 text-[10px]">
              Connected
            </Badge>
          </div>
          <Separator className="bg-zinc-800" />
          <div>
            <Button
              variant="ghost"
              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
              onClick={handleLogout}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Log Out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
