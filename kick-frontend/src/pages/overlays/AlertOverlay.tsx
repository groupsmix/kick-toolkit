import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface AlertEvent {
  type: "follow" | "subscribe" | "raid";
  username: string;
  message?: string;
  amount?: number;
}

/**
 * OBS Browser Source: Alert Box
 * URL: /overlay/alerts?token=xxx
 * Displays follow/sub/raid alerts with animations.
 */
export function AlertOverlay() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const [currentAlert, setCurrentAlert] = useState<AlertEvent | null>(null);
  const [visible, setVisible] = useState(false);
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

  // Demo alert on mount - in production this listens to WebSocket events
  useEffect(() => {
    if (error) return;
    const timer = setTimeout(() => {
      setCurrentAlert({ type: "follow", username: "new_viewer" });
      setVisible(true);
      setTimeout(() => setVisible(false), 5000);
    }, 2000);
    return () => clearTimeout(timer);
  }, [error]);

  if (error) {
    return (
      <div style={{ padding: 20, color: "#ef4444", fontFamily: "sans-serif", fontSize: 14 }}>
        Invalid or expired overlay token. Please regenerate in KickTools.
      </div>
    );
  }

  const alertConfig: Record<string, { emoji: string; label: string; color: string }> = {
    follow: { emoji: "💚", label: "New Follower!", color: "#10b981" },
    subscribe: { emoji: "⭐", label: "New Subscriber!", color: "#f59e0b" },
    raid: { emoji: "⚔️", label: "Raid!", color: "#8b5cf6" },
  };

  if (!currentAlert || !visible) return null;

  const config = alertConfig[currentAlert.type] || alertConfig.follow;

  return (
    <div
      style={{
        position: "fixed",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        fontFamily: "'Inter', sans-serif",
        textAlign: "center",
        animation: "alertBounce 0.5s ease-out",
      }}
    >
      <style>{`
        @keyframes alertBounce {
          0% { transform: translate(-50%, -50%) scale(0.3); opacity: 0; }
          50% { transform: translate(-50%, -50%) scale(1.05); }
          100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
        }
      `}</style>
      <div
        style={{
          background: "rgba(0, 0, 0, 0.85)",
          borderRadius: 16,
          padding: "32px 48px",
          border: `2px solid ${config.color}`,
          backdropFilter: "blur(12px)",
          boxShadow: `0 0 40px ${config.color}44`,
        }}
      >
        <div style={{ fontSize: 48, marginBottom: 12 }}>{config.emoji}</div>
        <div style={{ color: config.color, fontSize: 24, fontWeight: 800, marginBottom: 8 }}>
          {config.label}
        </div>
        <div style={{ color: "#ffffff", fontSize: 20, fontWeight: 600 }}>
          {currentAlert.username}
        </div>
        {currentAlert.message && (
          <div style={{ color: "#a1a1aa", fontSize: 14, marginTop: 8, maxWidth: 300 }}>
            {currentAlert.message}
          </div>
        )}
      </div>
    </div>
  );
}
