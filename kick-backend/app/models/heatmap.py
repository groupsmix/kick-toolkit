"""Viewer heatmap schemas."""

from pydantic import BaseModel
from typing import Optional


class ViewerSession(BaseModel):
    id: Optional[str] = None
    channel: str
    stream_session_id: Optional[str] = None
    username: str
    joined_at: str = ""
    left_at: Optional[str] = None
    duration_seconds: int = 0
    messages_sent: int = 0


class ContentSegment(BaseModel):
    id: Optional[str] = None
    channel: str
    stream_session_id: str
    label: str
    category: str = "general"
    started_at: str = ""
    ended_at: Optional[str] = None
    viewer_count_start: int = 0
    viewer_count_end: int = 0
    avg_viewers: float = 0.0
    retention_rate: float = 0.0
    chat_activity: int = 0


class ContentSegmentCreate(BaseModel):
    label: str
    category: str = "general"
    started_at: str = ""
    ended_at: Optional[str] = None
    viewer_count_start: int = 0
    viewer_count_end: int = 0


class HeatmapSnapshot(BaseModel):
    channel: str
    stream_session_id: str
    minute_offset: int = 0
    viewer_count: int = 0
    message_count: int = 0
    unique_chatters: int = 0
    category: str = ""


class HeatmapOverview(BaseModel):
    channel: str
    total_sessions: int = 0
    avg_session_duration: float = 0.0
    avg_retention_rate: float = 0.0
    peak_viewer_minute: int = 0
    best_category: str = ""
    worst_category: str = ""
    insights: list[dict] = []
    timeline: list[dict] = []
    segments: list[dict] = []
