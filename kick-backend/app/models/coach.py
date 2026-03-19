"""AI stream coach schemas."""

from pydantic import BaseModel
from typing import Optional


class CoachSettings(BaseModel):
    channel: str = ""
    enabled: bool = True
    engagement_alerts: bool = True
    game_duration_alerts: bool = True
    viewer_change_alerts: bool = True
    raid_welcome_alerts: bool = True
    sentiment_alerts: bool = True
    break_reminders: bool = True
    break_reminder_minutes: int = 120
    engagement_drop_threshold: float = 30.0
    viewer_change_threshold: int = 10


class StreamSession(BaseModel):
    id: Optional[str] = None
    channel: str
    status: str = "active"  # "active", "ended"
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    peak_viewers: int = 0
    avg_viewers: float = 0.0
    total_messages: int = 0
    game: str = ""


class CoachSuggestion(BaseModel):
    id: Optional[str] = None
    session_id: str
    channel: str
    type: str  # "engagement", "game_duration", "raid", "viewer_change", "sentiment", "break", "peak_moment"
    priority: str = "info"  # "info", "warning", "action"
    title: str
    message: str
    dismissed: bool = False
    created_at: Optional[str] = None
    dismissed_at: Optional[str] = None


class CoachAnalyzeRequest(BaseModel):
    channel: str
    session_id: str
    viewer_count: int = 0
    game: str = ""


class CoachAnalysisResult(BaseModel):
    suggestions: list[CoachSuggestion] = []
    metrics: dict = {}


class StreamSessionCreate(BaseModel):
    channel: str
    game: str = ""
