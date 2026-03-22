import { useState } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";

const PAGE_CONFIG: Record<string, { title: string; subtitle: string }> = {
  "/": { title: "Dashboard", subtitle: "Overview of your Kick channel" },
  "/dashboard": { title: "Dashboard", subtitle: "Overview of your Kick channel" },
  "/bot": { title: "Chat Bot & AI Moderation", subtitle: "Manage commands and auto-moderation" },
  "/chatlogs": { title: "Chat Logs", subtitle: "View and search chat history" },
  "/giveaway": { title: "Giveaway Roller", subtitle: "Create and manage giveaways" },
  "/antialt": { title: "Anti-Alt Detection", subtitle: "Detect and manage alt accounts" },
  "/anticheat": { title: "Anti-Cheat", subtitle: "Monitor for cheating behavior" },
  "/tournament": { title: "Tournament Organizer", subtitle: "Create brackets and manage tournaments" },
  "/ideas": { title: "Giveaway Ideas", subtitle: "Get inspiration for your next giveaway" },
  "/analytics": { title: "Predictive Analytics", subtitle: "Growth predictions and streamer stock market" },
  "/coach": { title: "AI Stream Coach", subtitle: "Real-time coaching to improve your stream" },
  "/clips": { title: "AI Clip Pipeline", subtitle: "Auto-detect and clip highlight moments" },
  "/heatmap": { title: "Viewer Heatmap", subtitle: "Visualize chat engagement over time" },
  "/loyalty": { title: "Loyalty & Points", subtitle: "Reward your community" },
  "/songs": { title: "Song Requests", subtitle: "Let viewers request songs" },
  "/schedule": { title: "Stream Schedule", subtitle: "Plan and share your streaming schedule" },
  "/overlays": { title: "OBS Overlays", subtitle: "Custom overlays for your stream" },
  "/polls": { title: "Chat Polls", subtitle: "Create polls for your audience" },
  "/predictions": { title: "Predictions", subtitle: "Let viewers predict outcomes" },
  "/translation": { title: "Translation", subtitle: "Real-time chat translation" },
  "/settings": { title: "Settings", subtitle: "Manage your account and preferences" },
  "/activity": { title: "Activity Log", subtitle: "Track all actions and events" },
  "/stream-intel": { title: "Stream Intel", subtitle: "Competitive intelligence and insights" },
  "/viewer-crm": { title: "Viewer CRM", subtitle: "Manage viewer relationships" },
  "/debrief": { title: "AI Debrief", subtitle: "Post-stream analysis and insights" },
  "/discord": { title: "Discord Bot", subtitle: "Manage your Discord integration" },
  "/revenue": { title: "Revenue", subtitle: "Track your earnings and monetization" },
  "/highlights": { title: "Highlights", subtitle: "Manage stream highlights" },
};

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { user } = useAuth();
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const pageConfig = PAGE_CONFIG[location.pathname] || PAGE_CONFIG["/"];

  return (
    <div className="flex h-screen bg-zinc-950 text-white overflow-hidden">
      {/* Desktop Sidebar */}
      <div className="hidden md:block">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {/* Mobile Sidebar Sheet */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="p-0 w-64 bg-zinc-950 border-zinc-800">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <Sidebar collapsed={false} onToggle={() => setMobileOpen(false)} onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title={pageConfig.title} subtitle={pageConfig.subtitle} user={user}>
          {/* Mobile menu button */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden text-zinc-400 hover:text-white"
            onClick={() => setMobileOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </Button>
        </Header>
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
