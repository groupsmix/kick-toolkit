import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { RouteErrorBoundary } from "@/components/RouteErrorBoundary";
import { PageSkeleton } from "@/components/LoadingSkeleton";
import { Toaster } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { Suspense, lazy } from "react";

// Eagerly loaded (needed immediately)
import { LandingPage } from "@/pages/LandingPage";
import { LoginPage } from "@/pages/LoginPage";
import { AuthCallbackPage } from "@/pages/AuthCallbackPage";

// Lazy-loaded pages
const DashboardPage = lazy(() => import("@/pages/DashboardPage").then(m => ({ default: m.DashboardPage })));
const BotPage = lazy(() => import("@/pages/BotPage").then(m => ({ default: m.BotPage })));
const ChatLogsPage = lazy(() => import("@/pages/ChatLogsPage").then(m => ({ default: m.ChatLogsPage })));
const GiveawayPage = lazy(() => import("@/pages/GiveawayPage").then(m => ({ default: m.GiveawayPage })));
const AntiAltPage = lazy(() => import("@/pages/AntiAltPage").then(m => ({ default: m.AntiAltPage })));
const AntiCheatPage = lazy(() => import("@/pages/AntiCheatPage").then(m => ({ default: m.AntiCheatPage })));
const TournamentPage = lazy(() => import("@/pages/TournamentPage").then(m => ({ default: m.TournamentPage })));
const IdeasPage = lazy(() => import("@/pages/IdeasPage").then(m => ({ default: m.IdeasPage })));
const AnalyticsPage = lazy(() => import("@/pages/AnalyticsPage").then(m => ({ default: m.AnalyticsPage })));
const StreamCoachPage = lazy(() => import("@/pages/StreamCoachPage").then(m => ({ default: m.StreamCoachPage })));
const ClipsPage = lazy(() => import("@/pages/ClipsPage").then(m => ({ default: m.ClipsPage })));
const HeatmapPage = lazy(() => import("@/pages/HeatmapPage").then(m => ({ default: m.HeatmapPage })));
const WhiteLabelPage = lazy(() => import("@/pages/WhiteLabelPage").then(m => ({ default: m.WhiteLabelPage })));
const LoyaltyPage = lazy(() => import("@/pages/LoyaltyPage").then(m => ({ default: m.LoyaltyPage })));
const SongRequestPage = lazy(() => import("@/pages/SongRequestPage").then(m => ({ default: m.SongRequestPage })));
const SchedulePage = lazy(() => import("@/pages/SchedulePage").then(m => ({ default: m.SchedulePage })));
const OverlaysPage = lazy(() => import("@/pages/OverlaysPage").then(m => ({ default: m.OverlaysPage })));
const MarketplacePage = lazy(() => import("@/pages/MarketplacePage").then(m => ({ default: m.MarketplacePage })));
const StreamIntelPage = lazy(() => import("@/pages/StreamIntelPage").then(m => ({ default: m.StreamIntelPage })));
const ViewerCRMPage = lazy(() => import("@/pages/ViewerCRMPage").then(m => ({ default: m.ViewerCRMPage })));
const DebriefPage = lazy(() => import("@/pages/DebriefPage").then(m => ({ default: m.DebriefPage })));
const DiscordBotPage = lazy(() => import("@/pages/DiscordBotPage").then(m => ({ default: m.DiscordBotPage })));
const RevenuePage = lazy(() => import("@/pages/RevenuePage").then(m => ({ default: m.RevenuePage })));
const HighlightsPage = lazy(() => import("@/pages/HighlightsPage").then(m => ({ default: m.HighlightsPage })));
const PollsPage = lazy(() => import("@/pages/PollsPage").then(m => ({ default: m.PollsPage })));
const PredictionsPage = lazy(() => import("@/pages/PredictionsPage").then(m => ({ default: m.PredictionsPage })));
const TranslationPage = lazy(() => import("@/pages/TranslationPage").then(m => ({ default: m.TranslationPage })));
const PricingPage = lazy(() => import("@/pages/PricingPage").then(m => ({ default: m.PricingPage })));
const TermsPage = lazy(() => import("@/pages/TermsPage").then(m => ({ default: m.TermsPage })));
const PrivacyPage = lazy(() => import("@/pages/PrivacyPage").then(m => ({ default: m.PrivacyPage })));
const DisclaimerPage = lazy(() => import("@/pages/DisclaimerPage").then(m => ({ default: m.DisclaimerPage })));
const PublicProfilePage = lazy(() => import("@/pages/PublicProfilePage").then(m => ({ default: m.PublicProfilePage })));

// Overlay pages (lightweight, but still lazy-loaded)
const ChatOverlay = lazy(() => import("@/pages/overlays/ChatOverlay").then(m => ({ default: m.ChatOverlay })));
const AlertOverlay = lazy(() => import("@/pages/overlays/AlertOverlay").then(m => ({ default: m.AlertOverlay })));
const GiveawayOverlay = lazy(() => import("@/pages/overlays/GiveawayOverlay").then(m => ({ default: m.GiveawayOverlay })));
const NowPlayingOverlay = lazy(() => import("@/pages/overlays/NowPlayingOverlay").then(m => ({ default: m.NowPlayingOverlay })));
const WordCloudOverlay = lazy(() => import("@/pages/overlays/WordCloudOverlay").then(m => ({ default: m.WordCloudOverlay })));

function PageSpinner() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-zinc-950">
      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

/** Suspense fallback that shows a content skeleton inside the app layout. */
function LayoutSkeleton() {
  return (
    <div className="p-6">
      <PageSkeleton />
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <PageSpinner />;
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
    return <PageSpinner />;
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

// Protected route definitions — path → lazy component
const protectedRoutes: { path: string; Component: React.LazyExoticComponent<React.ComponentType> }[] = [
  { path: "/dashboard", Component: DashboardPage },
  { path: "/bot", Component: BotPage },
  { path: "/chatlogs", Component: ChatLogsPage },
  { path: "/giveaway", Component: GiveawayPage },
  { path: "/antialt", Component: AntiAltPage },
  { path: "/anticheat", Component: AntiCheatPage },
  { path: "/tournament", Component: TournamentPage },
  { path: "/ideas", Component: IdeasPage },
  { path: "/analytics", Component: AnalyticsPage },
  { path: "/coach", Component: StreamCoachPage },
  { path: "/clips", Component: ClipsPage },
  { path: "/heatmap", Component: HeatmapPage },
  { path: "/whitelabel", Component: WhiteLabelPage },
  { path: "/loyalty", Component: LoyaltyPage },
  { path: "/songs", Component: SongRequestPage },
  { path: "/schedule", Component: SchedulePage },
  { path: "/overlays", Component: OverlaysPage },
  { path: "/marketplace", Component: MarketplacePage },
  { path: "/stream-intel", Component: StreamIntelPage },
  { path: "/viewer-crm", Component: ViewerCRMPage },
  { path: "/debrief", Component: DebriefPage },
  { path: "/discord", Component: DiscordBotPage },
  { path: "/revenue", Component: RevenuePage },
  { path: "/highlights", Component: HighlightsPage },
  { path: "/polls", Component: PollsPage },
  { path: "/predictions", Component: PredictionsPage },
  { path: "/translation", Component: TranslationPage },
];

function AppRoutes() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/disclaimer" element={<DisclaimerPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />

        {/* Protected app routes — generated from config */}
        {protectedRoutes.map(({ path, Component }) => (
          <Route
            key={path}
            path={path}
            element={
              <ProtectedRoute>
                <AppLayout>
                  <RouteErrorBoundary pageName={path.replace("/", "").replace(/-/g, " ")}>
                    <Suspense fallback={<LayoutSkeleton />}>
                      <Component />
                    </Suspense>
                  </RouteErrorBoundary>
                </AppLayout>
              </ProtectedRoute>
            }
          />
        ))}

        {/* Public routes - no auth required */}
        <Route path="/streamer/:channel" element={<PublicProfilePage />} />

        {/* OBS overlay widget routes - token-based auth, no login required */}
        <Route path="/overlay/chat" element={<ChatOverlay />} />
        <Route path="/overlay/alerts" element={<AlertOverlay />} />
        <Route path="/overlay/giveaway" element={<GiveawayOverlay />} />
        <Route path="/overlay/nowplaying" element={<NowPlayingOverlay />} />
        <Route path="/overlay/wordcloud" element={<WordCloudOverlay />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
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
