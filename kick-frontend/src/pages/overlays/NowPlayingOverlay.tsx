import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface NowPlayingState {
  title: string;
  artist: string;
  requested_by: string;
  is_playing: boolean;
}

/**
 * OBS Browser Source: Now Playing Widget
 * URL: /overlay/nowplaying?token=xxx
 * Shows current song from song request queue on stream.
 */
export function NowPlayingOverlay() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const [song, setSong] = useState<NowPlayingState | null>(null);
  const [error, setError] = useState(false);

  const fetchOverlayData = useCallback(async () => {
    if (!token) {
      setError(true);
      return;
    }
    try {
      const res = await fetch(`${API_URL}/api/overlays/render/${token}`);
      if (!res.ok) throw new Error("Invalid token");
      // Token is valid; in production this would also return current song data
    } catch {
      setError(true);
    }
  }, [token]);

  useEffect(() => {
    fetchOverlayData();
  }, [fetchOverlayData]);

  // Demo state - in production this polls the song queue API
  useEffect(() => {
    if (error) return;
    setSong({
      title: "Waiting for song...",
      artist: "",
      requested_by: "",
      is_playing: false,
    });
  }, [error]);

  if (error) {
    return (
      <div style={{ padding: 20, color: "#ef4444", fontFamily: "sans-serif", fontSize: 14 }}>
        Invalid or expired overlay token. Please regenerate in KickTools.
      </div>
    );
  }

  if (!song || !song.is_playing) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: 16,
        left: 16,
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <div
        style={{
          background: "rgba(0, 0, 0, 0.8)",
          borderRadius: 12,
          padding: "12px 20px",
          border: "1px solid rgba(168, 85, 247, 0.3)",
          backdropFilter: "blur(12px)",
          display: "flex",
          alignItems: "center",
          gap: 12,
          minWidth: 200,
          maxWidth: 400,
        }}
      >
        {/* Animated music icon */}
        <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height: 20, flexShrink: 0 }}>
          <style>{`
            @keyframes musicBar {
              0%, 100% { height: 4px; }
              50% { height: 16px; }
            }
          `}</style>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              style={{
                width: 3,
                borderRadius: 1,
                background: "#a855f7",
                animation: `musicBar 0.8s ease-in-out ${i * 0.15}s infinite`,
              }}
            />
          ))}
        </div>

        <div style={{ overflow: "hidden", flex: 1 }}>
          <div
            style={{
              color: "#ffffff",
              fontSize: 14,
              fontWeight: 600,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {song.title}
          </div>
          {song.artist && (
            <div
              style={{
                color: "#a1a1aa",
                fontSize: 12,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {song.artist}
            </div>
          )}
          {song.requested_by && (
            <div style={{ color: "#71717a", fontSize: 10, marginTop: 2 }}>
              Requested by {song.requested_by}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
