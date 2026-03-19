import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface GiveawayState {
  title: string;
  entries: number;
  status: "active" | "ended" | "idle";
  winner?: string;
  time_remaining?: number;
}

/**
 * OBS Browser Source: Giveaway Widget
 * URL: /overlay/giveaway?token=xxx
 * Shows active giveaway status on stream.
 */
export function GiveawayOverlay() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const [giveaway, setGiveaway] = useState<GiveawayState | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!token) {
      setError(true);
      return;
    }
    fetch(`${API_URL}/api/overlays/render/${token}`)
      .then((res) => {
        if (!res.ok) throw new Error("Invalid token");
      })
      .catch(() => setError(true));
  }, [token]);

  // Demo state - in production this polls the giveaway API
  useEffect(() => {
    if (error) return;
    setGiveaway({
      title: "Stream Giveaway",
      entries: 0,
      status: "idle",
    });
  }, [error]);

  if (error) {
    return (
      <div style={{ padding: 20, color: "#ef4444", fontFamily: "sans-serif", fontSize: 14 }}>
        Invalid or expired overlay token. Please regenerate in KickTools.
      </div>
    );
  }

  if (!giveaway || giveaway.status === "idle") return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 16,
        right: 16,
        fontFamily: "'Inter', sans-serif",
        minWidth: 240,
      }}
    >
      <div
        style={{
          background: "rgba(0, 0, 0, 0.8)",
          borderRadius: 12,
          padding: 16,
          border: "1px solid rgba(16, 185, 129, 0.3)",
          backdropFilter: "blur(12px)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <span style={{ fontSize: 18 }}>🎁</span>
          <span style={{ color: "#10b981", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1 }}>
            {giveaway.status === "active" ? "Giveaway Active" : "Winner!"}
          </span>
        </div>
        <div style={{ color: "#ffffff", fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
          {giveaway.title}
        </div>
        {giveaway.status === "active" && (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "#a1a1aa", fontSize: 13 }}>
              {giveaway.entries} entries
            </span>
            {giveaway.time_remaining !== undefined && giveaway.time_remaining > 0 && (
              <span style={{ color: "#f59e0b", fontSize: 13, fontWeight: 600 }}>
                {Math.floor(giveaway.time_remaining / 60)}:{String(giveaway.time_remaining % 60).padStart(2, "0")}
              </span>
            )}
          </div>
        )}
        {giveaway.winner && (
          <div
            style={{
              marginTop: 8,
              padding: "8px 12px",
              borderRadius: 8,
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              textAlign: "center",
            }}
          >
            <span style={{ color: "#10b981", fontSize: 18, fontWeight: 700 }}>
              🎉 {giveaway.winner}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
