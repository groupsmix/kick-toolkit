"""Stream intelligence, viewer CRM, debrief, discord, revenue, and highlights schemas."""

from pydantic import BaseModel
from typing import Optional


# ========== Stream Intelligence Dashboard ==========
class StreamIntelSession(BaseModel):
    id: Optional[str] = None
    channel: str
    started_at: str = ""
    ended_at: Optional[str] = None
    duration_minutes: int = 0
    peak_viewers: int = 0
    avg_viewers: float = 0.0
    chat_messages: int = 0
    new_followers: int = 0
    new_subscribers: int = 0
    stream_score: float = 0.0
    game: str = ""
    title: str = ""


class StreamScore(BaseModel):
    channel: str
    overall_score: float = 0.0
    viewer_score: float = 0.0
    chat_score: float = 0.0
    growth_score: float = 0.0
    consistency_score: float = 0.0
    trend: str = "stable"


class BestTimeSlot(BaseModel):
    day_of_week: int  # 0=Monday
    hour: int  # 0-23 UTC
    competition_score: float = 0.0
    recommended_score: float = 0.0
    avg_category_viewers: int = 0
    active_streamers: int = 0


class GameRecommendation(BaseModel):
    game: str
    growth_potential: float = 0.0
    competition_level: str = "medium"
    avg_viewers_in_category: int = 0
    trending: bool = False
    reason: str = ""


class StreamIntelOverview(BaseModel):
    channel: str
    stream_score: StreamScore
    recent_sessions: list[StreamIntelSession] = []
    best_times: list[BestTimeSlot] = []
    game_recommendations: list[GameRecommendation] = []
    weekly_summary: dict = {}


class StreamIntelSessionCreate(BaseModel):
    channel: str
    duration_minutes: int = 0
    peak_viewers: int = 0
    avg_viewers: float = 0.0
    chat_messages: int = 0
    new_followers: int = 0
    new_subscribers: int = 0
    game: str = ""
    title: str = ""


# ========== Viewer CRM ==========
class ViewerProfile(BaseModel):
    id: Optional[str] = None
    channel: str
    username: str
    first_seen: str = ""
    last_seen: str = ""
    total_messages: int = 0
    streams_watched: int = 0
    is_subscriber: bool = False
    is_follower: bool = False
    segment: str = "new"  # "super_fan", "regular", "at_risk", "new", "churned"
    watch_time_minutes: int = 0
    favorite_games: list[str] = []
    notes: str = ""


class ViewerSegmentSummary(BaseModel):
    segment: str
    count: int = 0
    avg_messages: float = 0.0
    avg_streams_watched: float = 0.0


class ViewerJourney(BaseModel):
    username: str
    channel: str
    milestones: list[dict] = []  # [{"event": "first_chat", "date": "...", "detail": "..."}]


class ViewerCRMOverview(BaseModel):
    channel: str
    total_viewers: int = 0
    segments: list[ViewerSegmentSummary] = []
    top_viewers: list[ViewerProfile] = []
    at_risk_viewers: list[ViewerProfile] = []
    shoutout_suggestions: list[ViewerProfile] = []
    churn_predictions: list[dict] = []


class ViewerProfileUpdate(BaseModel):
    notes: Optional[str] = None
    segment: Optional[str] = None


# ========== AI Post-Stream Debrief ==========
class DebriefRequest(BaseModel):
    channel: str
    session_id: Optional[str] = None


class DebriefResult(BaseModel):
    id: Optional[str] = None
    channel: str
    session_id: Optional[str] = None
    summary: str = ""
    top_moments: list[dict] = []
    sentiment_timeline: list[dict] = []
    chat_highlights: list[str] = []
    recommendations: list[str] = []
    title_suggestions: list[str] = []
    trending_topics: list[str] = []
    created_at: Optional[str] = None


# ========== Discord Bot Integration ==========
class DiscordBotConfig(BaseModel):
    id: Optional[str] = None
    channel: str
    guild_id: str = ""
    webhook_url: str = ""
    go_live_enabled: bool = True
    go_live_channel_id: str = ""
    go_live_message: str = "{streamer} is now live on Kick! Playing {game} - {title}"
    chat_bridge_enabled: bool = False
    chat_bridge_channel_id: str = ""
    sub_sync_enabled: bool = False
    sub_sync_role_id: str = ""
    stats_commands_enabled: bool = True
    schedule_display_enabled: bool = True
    schedule_channel_id: str = ""
    updated_at: Optional[str] = None


class DiscordBotConfigUpdate(BaseModel):
    guild_id: Optional[str] = None
    webhook_url: Optional[str] = None
    go_live_enabled: Optional[bool] = None
    go_live_channel_id: Optional[str] = None
    go_live_message: Optional[str] = None
    chat_bridge_enabled: Optional[bool] = None
    chat_bridge_channel_id: Optional[str] = None
    sub_sync_enabled: Optional[bool] = None
    sub_sync_role_id: Optional[str] = None
    stats_commands_enabled: Optional[bool] = None
    schedule_display_enabled: Optional[bool] = None
    schedule_channel_id: Optional[str] = None


class DiscordBotStatus(BaseModel):
    channel: str
    connected: bool = False
    guild_name: str = ""
    features_active: list[str] = []
    last_ping: Optional[str] = None


# ========== Revenue Intelligence ==========
class RevenueEntry(BaseModel):
    id: Optional[str] = None
    channel: str
    source: str  # "subscription", "tip", "sponsor", "merch", "other"
    amount: float = 0.0
    currency: str = "USD"
    description: str = ""
    stream_session_id: Optional[str] = None
    date: str = ""
    created_at: Optional[str] = None


class RevenueEntryCreate(BaseModel):
    source: str
    amount: float
    currency: str = "USD"
    description: str = ""
    stream_session_id: Optional[str] = None
    date: str = ""


class RevenueSummary(BaseModel):
    channel: str
    total_revenue: float = 0.0
    total_this_month: float = 0.0
    total_last_month: float = 0.0
    month_over_month_change: float = 0.0
    by_source: list[dict] = []  # [{"source": "subscription", "total": 500.0}]
    monthly_totals: list[dict] = []  # [{"month": "2026-03", "total": 1200.0}]
    per_stream: list[dict] = []  # [{"session_id": "...", "revenue": 45.0, "date": "..."}]
    forecast_next_month: float = 0.0


# ========== Auto-Highlight Detection ==========
class HighlightMarker(BaseModel):
    id: Optional[str] = None
    channel: str
    session_id: Optional[str] = None
    timestamp_offset_seconds: int = 0
    intensity: float = 0.0  # 0-100
    message_rate: float = 0.0  # messages per second at peak
    duration_seconds: int = 30
    description: str = ""
    sample_messages: list[str] = []
    category: str = "hype"  # "hype", "funny", "clutch", "fail", "emotional"
    created_at: Optional[str] = None


class HighlightSummary(BaseModel):
    channel: str
    session_id: Optional[str] = None
    total_highlights: int = 0
    peak_moment: Optional[HighlightMarker] = None
    highlights: list[HighlightMarker] = []
    stream_summary: str = ""
