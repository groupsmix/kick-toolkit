import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Gift,
  ShieldAlert,
  Trophy,
  Lightbulb,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface SidebarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  collapsed: boolean;
  onToggle: () => void;
}

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "bot", label: "Chat Bot & AI Mod", icon: Bot },
  { id: "chatlogs", label: "Chat Logs", icon: MessageSquare },
  { id: "giveaway", label: "Giveaway Roller", icon: Gift },
  { id: "antialt", label: "Anti-Alt Detection", icon: ShieldAlert, premium: true },
  { id: "tournament", label: "Tournament", icon: Trophy },
  { id: "ideas", label: "Giveaway Ideas", icon: Lightbulb },
];

export function Sidebar({ currentPage, onNavigate, collapsed, onToggle }: SidebarProps) {
  return (
    <div
      className={cn(
        "flex flex-col h-screen bg-zinc-950 border-r border-zinc-800 transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500">
          <Zap className="w-5 h-5 text-black" />
        </div>
        {!collapsed && (
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">KickTools</h1>
            <p className="text-[10px] text-zinc-500 uppercase tracking-widest">Streamer Toolkit</p>
          </div>
        )}
      </div>

      <Separator className="bg-zinc-800" />

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                  : "text-zinc-400 hover:text-white hover:bg-zinc-800/50",
                collapsed && "justify-center px-0"
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon className={cn("w-5 h-5 flex-shrink-0", isActive && "text-emerald-400")} />
              {!collapsed && (
                <span className="flex-1 text-left">{item.label}</span>
              )}
              {!collapsed && item.premium && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-amber-500/20 text-amber-400 uppercase">
                  Pro
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <Separator className="bg-zinc-800" />

      {/* Collapse toggle */}
      <div className="p-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className="w-full text-zinc-500 hover:text-white hover:bg-zinc-800"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          {!collapsed && <span className="ml-2 text-xs">Collapse</span>}
        </Button>
      </div>
    </div>
  );
}
