import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, Search, LogOut, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import type { KickUser } from "@/types";

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
};

export function Header({ title, subtitle, user, children }: HeaderProps) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [showNotifications, setShowNotifications] = useState(false);

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
            onClick={() => setShowNotifications(!showNotifications)}
          >
            <Bell className="w-5 h-5" />
          </Button>

          {showNotifications && (
            <div className="absolute right-0 top-full mt-2 w-72 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl z-50">
              <div className="flex items-center justify-between p-3 border-b border-zinc-800">
                <span className="text-sm font-medium text-white">Notifications</span>
                <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-400" onClick={() => setShowNotifications(false)}>
                  <X className="w-3 h-3" />
                </Button>
              </div>
              <div className="p-4 text-center">
                <p className="text-xs text-zinc-500">No new notifications</p>
              </div>
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
