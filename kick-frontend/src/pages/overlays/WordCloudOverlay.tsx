import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface WordEntry {
  word: string;
  count: number;
  weight: number;
}

interface WordCloudData {
  channel: string;
  minutes: number;
  total_messages: number;
  words: WordEntry[];
}

const COLORS = [
  "#10b981", "#6366f1", "#f59e0b", "#ec4899", "#3b82f6",
  "#8b5cf6", "#14b8a6", "#f97316", "#06b6d4", "#ef4444",
  "#84cc16", "#e879f9",
];

export function WordCloudOverlay() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const [data, setData] = useState<WordCloudData | null>(null);
  const [overlayConfig, setOverlayConfig] = useState<{
    channel: string;
    config: Record<string, unknown>;
  } | null>(null);

  // Fetch overlay config by token
  useEffect(() => {
    if (!token) return;
    fetch(`${API_URL}/api/overlays/render/${token}`)
      .then((r) => r.json())
      .then(setOverlayConfig)
      .catch(() => {});
  }, [token]);

  const fetchWords = useCallback(async () => {
    if (!overlayConfig?.channel) return;
    try {
      const res = await fetch(
        `${API_URL}/api/overlays/wordcloud/${overlayConfig.channel}?minutes=30&max_words=80`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("kick_session_id") || ""}`,
          },
        }
      );
      if (res.ok) {
        const d = await res.json();
        setData(d);
      }
    } catch {
      // silently retry on next interval
    }
  }, [overlayConfig?.channel]);

  useEffect(() => {
    fetchWords();
    const interval = setInterval(fetchWords, 20_000);
    return () => clearInterval(interval);
  }, [fetchWords]);

  if (!data || !data.words.length) {
    return (
      <div
        style={{
          width: "100vw",
          height: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "transparent",
          fontFamily: "'Inter', sans-serif",
          color: "#52525b",
        }}
      >
        Waiting for chat data...
      </div>
    );
  }

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        justifyContent: "center",
        gap: "8px",
        padding: "20px",
        background: "transparent",
        fontFamily: "'Inter', sans-serif",
        overflow: "hidden",
      }}
    >
      {data.words.map((w, i) => {
        const fontSize = 14 + w.weight * 48;
        const color = COLORS[i % COLORS.length];
        const rotation = Math.random() > 0.7 ? (Math.random() > 0.5 ? 90 : -90) : 0;
        return (
          <span
            key={w.word}
            style={{
              fontSize: `${fontSize}px`,
              fontWeight: w.weight > 0.5 ? 700 : 400,
              color,
              opacity: 0.7 + w.weight * 0.3,
              transform: `rotate(${rotation}deg)`,
              display: "inline-block",
              padding: "2px 6px",
              transition: "all 0.5s ease",
            }}
          >
            {w.word}
          </span>
        );
      })}
    </div>
  );
}
