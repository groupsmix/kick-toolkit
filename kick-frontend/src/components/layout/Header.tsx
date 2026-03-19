import { Bell, Search, LogOut } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

interface KickUser {
  user_id?: number;
  name?: string;
  email?: string;
  profile_picture?: string;
  [key: string]: unknown;
}

interface HeaderProps {
  title: string;
  subtitle?: string;
  user?: KickUser | null;
  children?: React.ReactNode;
}

export function Header({ title, subtitle, user, children }: HeaderProps) {
  const { logout } = useAuth();

  const displayName = user?.name || "Streamer";
  const initials = displayName.slice(0, 2).toUpperCase();
  const profilePic = user?.profile_picture;

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
        <div className="relative hidden sm:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <Input
            placeholder="Search..."
            className="w-64 pl-9 bg-zinc-900 border-zinc-700 text-white placeholder:text-zinc-500 focus:border-emerald-500"
          />
        </div>

        <Button variant="ghost" size="icon" className="relative text-zinc-400 hover:text-white">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-emerald-500" />
        </Button>

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
