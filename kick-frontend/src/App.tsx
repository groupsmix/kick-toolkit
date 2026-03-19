import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { DashboardPage } from "@/pages/DashboardPage";
import { BotPage } from "@/pages/BotPage";
import { ChatLogsPage } from "@/pages/ChatLogsPage";
import { GiveawayPage } from "@/pages/GiveawayPage";
import { AntiAltPage } from "@/pages/AntiAltPage";
import { TournamentPage } from "@/pages/TournamentPage";
import { IdeasPage } from "@/pages/IdeasPage";

const PAGE_CONFIG: Record<string, { title: string; subtitle: string }> = {
  dashboard: { title: "Dashboard", subtitle: "Overview of your Kick channel" },
  bot: { title: "Chat Bot & AI Moderation", subtitle: "Manage commands and auto-moderation" },
  chatlogs: { title: "Chat Logs", subtitle: "View and search chat history" },
  giveaway: { title: "Giveaway Roller", subtitle: "Create and manage giveaways" },
  antialt: { title: "Anti-Alt Detection", subtitle: "Detect and manage alt accounts" },
  tournament: { title: "Tournament Organizer", subtitle: "Create brackets and manage tournaments" },
  ideas: { title: "Giveaway Ideas", subtitle: "Get inspiration for your next giveaway" },
};

function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const pageConfig = PAGE_CONFIG[currentPage] || PAGE_CONFIG.dashboard;

  const renderPage = () => {
    switch (currentPage) {
      case "dashboard": return <DashboardPage />;
      case "bot": return <BotPage />;
      case "chatlogs": return <ChatLogsPage />;
      case "giveaway": return <GiveawayPage />;
      case "antialt": return <AntiAltPage />;
      case "tournament": return <TournamentPage />;
      case "ideas": return <IdeasPage />;
      default: return <DashboardPage />;
    }
  };

  return (
    <div className="flex h-screen bg-zinc-950 text-white overflow-hidden">
      <Sidebar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title={pageConfig.title} subtitle={pageConfig.subtitle} />
        <main className="flex-1 overflow-y-auto p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

export default App;
