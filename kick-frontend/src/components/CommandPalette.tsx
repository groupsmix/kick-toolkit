import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Gift,
  Trophy,
  Vote,
  TrendingUp,
  Star,
  Calendar,
  Monitor,
  ShieldAlert,
  BarChart3,
  Brain,
  MessageCircle,
  Settings,
  ClipboardList,
  Search,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface CommandItem {
  label: string;
  path: string;
  icon: LucideIcon;
  keywords?: string;
}

const commands: CommandItem[] = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard, keywords: "home overview" },
  { label: "Chat Bot & AI Mod", path: "/bot", icon: Bot, keywords: "commands moderation" },
  { label: "Chat Logs", path: "/chatlogs", icon: MessageSquare, keywords: "messages history search" },
  { label: "Giveaway Roller", path: "/giveaway", icon: Gift, keywords: "raffle prize winner" },
  { label: "Tournament", path: "/tournament", icon: Trophy, keywords: "bracket match competition" },
  { label: "Chat Polls", path: "/polls", icon: Vote, keywords: "vote survey" },
  { label: "Predictions", path: "/predictions", icon: TrendingUp, keywords: "bet outcome" },
  { label: "Loyalty & Points", path: "/loyalty", icon: Star, keywords: "rewards currency" },
  { label: "Stream Schedule", path: "/schedule", icon: Calendar, keywords: "calendar plan" },
  { label: "OBS Overlays", path: "/overlays", icon: Monitor, keywords: "widgets alerts" },
  { label: "Anti-Alt Detection", path: "/antialt", icon: ShieldAlert, keywords: "alt accounts ban" },
  { label: "Analytics", path: "/analytics", icon: BarChart3, keywords: "stats growth data" },
  { label: "AI Stream Coach", path: "/coach", icon: Brain, keywords: "tips advice improve" },
  { label: "Discord Bot", path: "/discord", icon: MessageCircle, keywords: "integration server" },
  { label: "Settings", path: "/settings", icon: Settings, keywords: "account preferences notifications" },
  { label: "Activity Log", path: "/activity", icon: ClipboardList, keywords: "audit history events" },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const filtered = query
    ? commands.filter((cmd) => {
        const q = query.toLowerCase();
        return (
          cmd.label.toLowerCase().includes(q) ||
          cmd.path.toLowerCase().includes(q) ||
          (cmd.keywords && cmd.keywords.toLowerCase().includes(q))
        );
      })
    : commands;

  const handleSelect = useCallback(
    (item: CommandItem) => {
      setOpen(false);
      setQuery("");
      navigate(item.path);
    },
    [navigate],
  );

  // Global keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Scroll selected item into view
  useEffect(() => {
    if (!listRef.current) return;
    const items = listRef.current.querySelectorAll("[data-cmd-item]");
    items[selectedIndex]?.scrollIntoView({ block: "nearest" });
  }, [selectedIndex]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, 0));
    } else if (e.key === "Enter" && filtered[selectedIndex]) {
      e.preventDefault();
      handleSelect(filtered[selectedIndex]);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-md p-0 gap-0 bg-zinc-900 border-zinc-700 overflow-hidden">
        <DialogTitle className="sr-only">Command Palette</DialogTitle>
        <div className="flex items-center gap-2 px-3 border-b border-zinc-800">
          <Search className="w-4 h-4 text-zinc-500 flex-shrink-0" />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search pages..."
            className="border-0 bg-transparent text-white placeholder:text-zinc-500 focus-visible:ring-0 h-12"
            autoFocus
          />
          <kbd className="hidden sm:inline-flex h-5 items-center gap-0.5 rounded border border-zinc-700 bg-zinc-800 px-1.5 text-[10px] font-medium text-zinc-400">
            ESC
          </kbd>
        </div>
        <div ref={listRef} className="max-h-72 overflow-y-auto py-2">
          {filtered.length === 0 ? (
            <p className="text-center text-sm text-zinc-500 py-6">No results found</p>
          ) : (
            filtered.map((cmd, i) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={cmd.path}
                  data-cmd-item
                  onClick={() => handleSelect(cmd)}
                  onMouseEnter={() => setSelectedIndex(i)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                    i === selectedIndex
                      ? "bg-emerald-500/10 text-emerald-400"
                      : "text-zinc-300 hover:bg-zinc-800/50"
                  }`}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <span>{cmd.label}</span>
                </button>
              );
            })
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
