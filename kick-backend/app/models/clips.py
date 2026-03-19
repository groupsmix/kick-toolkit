"""AI clip pipeline schemas."""

from pydantic import BaseModel
from typing import Optional


class HypeMoment(BaseModel):
    id: Optional[str] = None
    channel: str
    session_id: Optional[str] = None
    timestamp_start: str = ""
    timestamp_end: str = ""
    intensity: float = 0.0
    trigger_type: str = "chat_spike"
    message_count: int = 0
    peak_rate: float = 0.0
    sample_messages: list[str] = []
    status: str = "detected"
    created_at: Optional[str] = None


class GeneratedClip(BaseModel):
    id: Optional[str] = None
    channel: str
    hype_moment_id: Optional[str] = None
    title: str = ""
    description: str = ""
    caption: str = ""
    file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    duration_seconds: float = 0.0
    status: str = "pending"
    platform_specs: dict = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ClipCreate(BaseModel):
    channel: str
    hype_moment_id: Optional[str] = None
    title: str = ""
    description: str = ""
    duration_seconds: float = 0.0


class ClipPost(BaseModel):
    id: Optional[str] = None
    clip_id: str
    platform: str  # "tiktok", "youtube", "instagram"
    platform_post_id: Optional[str] = None
    post_url: Optional[str] = None
    status: str = "pending"
    caption: str = ""
    error_message: Optional[str] = None
    posted_at: Optional[str] = None
    created_at: Optional[str] = None


class ClipPostRequest(BaseModel):
    platform: str  # "tiktok", "youtube", "instagram"
    caption: str = ""


class ClipCaptionRequest(BaseModel):
    style: str = "engaging"  # "engaging", "funny", "informative", "trending"
