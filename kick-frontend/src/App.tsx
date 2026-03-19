import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { Toaster } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { BotPage } from "@/pages/BotPage";
import { ChatLogsPage } from "@/pages/ChatLogsPage";
import { GiveawayPage } from "@/pages/GiveawayPage";
import { AntiAltPage } from "@/pages/AntiAltPage";
import { TournamentPage } from "@/pages/TournamentPage";
import { IdeasPage } from "@/pages/IdeasPage";
import { LoginPage } from "@/pages/LoginPage";
import { AuthCallbackPage } from "@/pages/AuthCallbackPage";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/bot" element={<BotPage />} />
                <Route path="/chatlogs" element={<ChatLogsPage />} />
                <Route path="/giveaway" element={<GiveawayPage />} />
                <Route path="/antialt" element={<AntiAltPage />} />
                <Route path="/tournament" element={<TournamentPage />} />
                <Route path="/ideas" element={<IdeasPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: "#18181b",
              border: "1px solid #27272a",
              color: "#fff",
            },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
