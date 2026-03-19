import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Toaster } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { BotPage } from "@/pages/BotPage";
import { ChatLogsPage } from "@/pages/ChatLogsPage";
import { GiveawayPage } from "@/pages/GiveawayPage";
import { AntiAltPage } from "@/pages/AntiAltPage";
import { AntiCheatPage } from "@/pages/AntiCheatPage";
import { TournamentPage } from "@/pages/TournamentPage";
import { IdeasPage } from "@/pages/IdeasPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { StreamCoachPage } from "@/pages/StreamCoachPage";
import { ClipsPage } from "@/pages/ClipsPage";
import { HeatmapPage } from "@/pages/HeatmapPage";
import { WhiteLabelPage } from "@/pages/WhiteLabelPage";
import { LoyaltyPage } from "@/pages/LoyaltyPage";
import { SongRequestPage } from "@/pages/SongRequestPage";
import { SchedulePage } from "@/pages/SchedulePage";
import { OverlaysPage } from "@/pages/OverlaysPage";
import { PublicProfilePage } from "@/pages/PublicProfilePage";
import { ChatOverlay } from "@/pages/overlays/ChatOverlay";
import { AlertOverlay } from "@/pages/overlays/AlertOverlay";
import { GiveawayOverlay } from "@/pages/overlays/GiveawayOverlay";
import { NowPlayingOverlay } from "@/pages/overlays/NowPlayingOverlay";
import { MarketplacePage } from "@/pages/MarketplacePage";
import { StreamIntelPage } from "@/pages/StreamIntelPage";
import { ViewerCRMPage } from "@/pages/ViewerCRMPage";
import { DebriefPage } from "@/pages/DebriefPage";
import { DiscordBotPage } from "@/pages/DiscordBotPage";
import { RevenuePage } from "@/pages/RevenuePage";
import { HighlightsPage } from "@/pages/HighlightsPage";
import { LoginPage } from "@/pages/LoginPage";
import { AuthCallbackPage } from "@/pages/AuthCallbackPage";
import { LandingPage } from "@/pages/LandingPage";
import { PricingPage } from "@/pages/PricingPage";
import { TermsPage } from "@/pages/TermsPage";
import { PrivacyPage } from "@/pages/PrivacyPage";
import { DisclaimerPage } from "@/pages/DisclaimerPage";

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

/** Show landing page for unauthenticated users, dashboard for authenticated */
function HomePage() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LandingPage />;
  }

  return (
    <AppLayout>
      <DashboardPage />
    </AppLayout>
  );
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<HomePage />} />
      <Route path="/pricing" element={<PricingPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="/disclaimer" element={<DisclaimerPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />

      {/* Protected app routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <AppLayout>
              <DashboardPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/bot"
        element={
          <ProtectedRoute>
            <AppLayout>
              <BotPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/chatlogs"
        element={
          <ProtectedRoute>
            <AppLayout>
              <ChatLogsPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/giveaway"
        element={
          <ProtectedRoute>
            <AppLayout>
              <GiveawayPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/antialt"
        element={
          <ProtectedRoute>
            <AppLayout>
              <AntiAltPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/anticheat"
        element={
          <ProtectedRoute>
            <AppLayout>
              <AntiCheatPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/tournament"
        element={
          <ProtectedRoute>
            <AppLayout>
              <TournamentPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/ideas"
        element={
          <ProtectedRoute>
            <AppLayout>
              <IdeasPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute>
            <AppLayout>
              <AnalyticsPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/coach"
        element={
          <ProtectedRoute>
            <AppLayout>
              <StreamCoachPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/clips"
        element={
          <ProtectedRoute>
            <AppLayout>
              <ClipsPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/heatmap"
        element={
          <ProtectedRoute>
            <AppLayout>
              <HeatmapPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/whitelabel"
        element={
          <ProtectedRoute>
            <AppLayout>
              <WhiteLabelPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/loyalty"
        element={
          <ProtectedRoute>
            <AppLayout>
              <LoyaltyPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/songs"
        element={
          <ProtectedRoute>
            <AppLayout>
              <SongRequestPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/schedule"
        element={
          <ProtectedRoute>
            <AppLayout>
              <SchedulePage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/overlays"
        element={
          <ProtectedRoute>
            <AppLayout>
              <OverlaysPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/marketplace"
        element={
          <ProtectedRoute>
            <AppLayout>
              <MarketplacePage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/stream-intel"
        element={
          <ProtectedRoute>
            <AppLayout>
              <StreamIntelPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/viewer-crm"
        element={
          <ProtectedRoute>
            <AppLayout>
              <ViewerCRMPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/debrief"
        element={
          <ProtectedRoute>
            <AppLayout>
              <DebriefPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/discord"
        element={
          <ProtectedRoute>
            <AppLayout>
              <DiscordBotPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/revenue"
        element={
          <ProtectedRoute>
            <AppLayout>
              <RevenuePage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/highlights"
        element={
          <ProtectedRoute>
            <AppLayout>
              <HighlightsPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      {/* Public routes - no auth required */}
      <Route path="/streamer/:channel" element={<PublicProfilePage />} />

      {/* OBS overlay widget routes - token-based auth, no login required */}
      <Route path="/overlay/chat" element={<ChatOverlay />} />
      <Route path="/overlay/alerts" element={<AlertOverlay />} />
      <Route path="/overlay/giveaway" element={<GiveawayOverlay />} />
      <Route path="/overlay/nowplaying" element={<NowPlayingOverlay />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
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
      </QueryClientProvider>
    </BrowserRouter>
  );
}

export default App;
