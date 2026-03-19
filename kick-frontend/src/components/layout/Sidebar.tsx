import { useNavigate, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Gift,
  ShieldAlert,
  ShieldCheck,
  Trophy,
  Lightbulb,
  ChevronLeft,
  ChevronRight,
  Zap,
  BarChart3,
  Brain,
  Scissors,
  Map,
  Building2,
  Store,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  onNavigate?: () => void;
}

const navItems = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard },
  { path: "/bot", label: "Chat Bot & AI Mod", icon: Bot },
  { path: "/chatlogs", label: "Chat Logs", icon: MessageSquare },
  { path: "/giveaway", label: "Giveaway Roller", icon: Gift },
  { path: "/antialt", label: "Anti-Alt Detection", icon: ShieldAlert, premium: true },
  { path: "/anticheat", label: "Anti-Cheat", icon: ShieldCheck, premium: true },
  { path: "/tournament", label: "Tournament", icon: Trophy },
  { path: "/ideas", label: "Giveaway Ideas", icon: Lightbulb },
  { path: "/analytics", label: "Predictive Analytics", icon: BarChart3, premium: true },
  { path: "/coach", label: "AI Stream Coach", icon: Brain, premium: true },
  { path: "/clips", label: "AI Clip Pipeline", icon: Scissors, premium: true },
  { path: "/heatmap", label: "Viewer Heatmap", icon: Map, premium: true },
  { path: "/whitelabel", label: "White-Label", icon: Building2, premium: true },
  { path: "/marketplace", label: "Marketplace", icon: Store },
];

export function Sidebar({ collapsed, onToggle, onNavigate }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
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
          const isActive = location.pathname === item.path;
          return (
            <button
              key={item.path}
              onClick={() => { navigate(item.path); onNavigate?.(); }}
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
