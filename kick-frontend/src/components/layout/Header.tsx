import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, Search, LogOut, X, ShieldAlert, Gift, Trophy, Bot, Info } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import type { KickUser } from "@/types";

interface Notification {
  id: string;
  type: "moderation" | "giveaway" | "tournament" | "bot" | "info";
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

function getStoredNotifications(): Notification[] {
  try {
    const stored = localStorage.getItem("kicktools_notifications");
    if (stored) return JSON.parse(stored);
  } catch {
    // ignore parse errors
  }
  // Default welcome notifications for new users
  return [
    {
      id: "welcome-1",
      type: "info",
      title: "Welcome to KickTools!",
      message: "Get started by setting up your first bot command.",
      timestamp: new Date().toISOString(),
      read: false,
    },
    {
      id: "welcome-2",
      type: "info",
      title: "Tip: Check Settings",
      message: "Configure your notification preferences in Settings.",
      timestamp: new Date().toISOString(),
      read: false,
    },
  ];
}

const notificationIcons: Record<Notification["type"], React.ElementType> = {
  moderation: ShieldAlert,
  giveaway: Gift,
  tournament: Trophy,
  bot: Bot,
  info: Info,
};

const notificationColors: Record<Notification["type"], string> = {
  moderation: "text-red-400",
  giveaway: "text-emerald-400",
  tournament: "text-amber-400",
  bot: "text-cyan-400",
  info: "text-blue-400",
};

interface HeaderProps {
  title: string;
  subtitle?: string;
  user?: KickUser | null;
  children?: React.ReactNode;
}

const PAGE_ROUTES: Record<string, string> = {
  bot: "/bot",
  chat: "/chatlogs",
  logs: "/chatlogs",
  giveaway: "/giveaway",
  tournament: "/tournament",
  antialt: "/antialt",
  alt: "/antialt",
  ideas: "/ideas",
  dashboard: "/",
  settings: "/settings",
  analytics: "/analytics",
  polls: "/polls",
  schedule: "/schedule",
};

export function Header({ title, subtitle, user, children }: HeaderProps) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>(getStoredNotifications);

  const unreadCount = notifications.filter((n) => !n.read).length;

  useEffect(() => {
    localStorage.setItem("kicktools_notifications", JSON.stringify(notifications));
  }, [notifications]);

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const dismissNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
    setShowNotifications(false);
  };

  const displayName = user?.name || "Streamer";
  const initials = displayName.slice(0, 2).toUpperCase();
  const profilePic = user?.profile_picture;

  const handleSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const q = searchQuery.trim().toLowerCase();
      if (!q) return;
      for (const [keyword, route] of Object.entries(PAGE_ROUTES)) {
        if (q.includes(keyword)) {
          navigate(route);
          setSearchQuery("");
          return;
        }
      }
    },
    [searchQuery, navigate],
  );

  const formatNotifTime = (ts: string) => {
    const diff = Date.now() - new Date(ts).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <header className="flex items-center justify-between px-4 sm:px-6 py-4 border-b border-zinc-800 bg-zinc-950/50 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        {children}
        <div>
          <h2 className="text-xl font-bold text-white">{title}</h2>
          {subtitle && <p className="text-sm text-zinc-500">{subtitle}</p>}
        </div>
      </div>

      <div className="flex items-center gap-4">
        <form onSubmit={handleSearch} className="relative hidden sm:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Navigate to page..."
            className="w-64 pl-9 bg-zinc-900 border-zinc-700 text-white placeholder:text-zinc-500 focus:border-emerald-500"
          />
        </form>

        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="relative text-zinc-400 hover:text-white"
            onClick={() => {
              setShowNotifications(!showNotifications);
              if (!showNotifications) markAllRead();
            }}
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full text-[10px] font-bold text-white flex items-center justify-center">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </Button>

          {showNotifications && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl z-50">
              <div className="flex items-center justify-between p-3 border-b border-zinc-800">
                <span className="text-sm font-medium text-white">Notifications</span>
                <div className="flex items-center gap-1">
                  {notifications.length > 0 && (
                    <Button variant="ghost" size="sm" className="h-6 text-[10px] text-zinc-500 hover:text-zinc-300 px-2" onClick={clearAll}>
                      Clear all
                    </Button>
                  )}
                  <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-400" onClick={() => setShowNotifications(false)}>
                    <X className="w-3 h-3" />
                  </Button>
                </div>
              </div>
              {notifications.length === 0 ? (
                <div className="p-6 text-center">
                  <Bell className="w-8 h-8 text-zinc-700 mx-auto mb-2" />
                  <p className="text-xs text-zinc-500">No notifications</p>
                </div>
              ) : (
                <div className="max-h-80 overflow-y-auto">
                  {notifications.map((notif) => {
                    const Icon = notificationIcons[notif.type];
                    const color = notificationColors[notif.type];
                    return (
                      <div
                        key={notif.id}
                        className={`flex items-start gap-3 p-3 border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors ${
                          !notif.read ? "bg-zinc-800/20" : ""
                        }`}
                      >
                        <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${color}`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-white">{notif.title}</p>
                          <p className="text-[11px] text-zinc-500 mt-0.5 line-clamp-2">{notif.message}</p>
                          <p className="text-[10px] text-zinc-600 mt-1">{formatNotifTime(notif.timestamp)}</p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-5 w-5 text-zinc-600 hover:text-zinc-400 flex-shrink-0"
                          onClick={() => dismissNotification(notif.id)}
                        >
                          <X className="w-3 h-3" />
                        </Button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Avatar className="w-8 h-8">
            {profilePic && <AvatarImage src={profilePic} alt={displayName} />}
            <AvatarFallback className="bg-emerald-500/20 text-emerald-400 text-sm font-bold">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-white">{displayName}</p>
            <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-emerald-500/30 text-emerald-400">
              Connected
            </Badge>
          </div>
        </div>

        <Button
          variant="ghost"
          size="icon"
          onClick={logout}
          className="text-zinc-500 hover:text-red-400 hover:bg-red-500/10"
          title="Disconnect"
        >
          <LogOut className="w-4 h-4" />
        </Button>
      </div>
    </header>
  );
}
