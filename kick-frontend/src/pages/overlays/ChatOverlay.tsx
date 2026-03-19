import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface ChatMessage {
  username: string;
  content: string;
  color: string;
  timestamp: number;
}

/**
 * OBS Browser Source: Chat Overlay
 * URL: /overlay/chat?token=xxx
 * Displays live chat messages styled for on-stream display.
 */
export function ChatOverlay() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState(false);

  // Validate token on mount
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

  // Simulate incoming messages for demo / placeholder
  // In production, this would connect to a WebSocket for real-time chat
  useEffect(() => {
    if (error) return;
    const demo: ChatMessage[] = [
      { username: "viewer1", content: "Great stream!", color: "#10b981", timestamp: Date.now() },
      { username: "mod_user", content: "Welcome everyone!", color: "#f59e0b", timestamp: Date.now() + 1000 },
    ];
    setMessages(demo);
  }, [error]);

  if (error) {
    return (
      <div style={{ padding: 20, color: "#ef4444", fontFamily: "sans-serif", fontSize: 14 }}>
        Invalid or expired overlay token. Please regenerate in KickTools.
      </div>
    );
  }

  return (
    <div
      style={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        padding: 16,
        fontFamily: "'Inter', sans-serif",
        background: "transparent",
        overflow: "hidden",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              background: "rgba(0, 0, 0, 0.6)",
              borderRadius: 6,
              padding: "6px 12px",
              display: "inline-flex",
              gap: 8,
              alignItems: "baseline",
              backdropFilter: "blur(8px)",
              maxWidth: "100%",
            }}
          >
            <span style={{ color: msg.color, fontWeight: 700, fontSize: 14, whiteSpace: "nowrap" }}>
              {msg.username}
            </span>
            <span style={{ color: "#e4e4e7", fontSize: 14, wordBreak: "break-word" }}>
              {msg.content}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
