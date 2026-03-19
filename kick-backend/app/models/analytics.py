"""Analytics and prediction schemas."""

from pydantic import BaseModel
from typing import Optional


class StreamerSnapshot(BaseModel):
    id: Optional[str] = None
    channel: str
    avg_viewers: float = 0.0
    peak_viewers: int = 0
    follower_count: int = 0
    subscriber_count: int = 0
    hours_streamed: float = 0.0
    chat_messages: int = 0
    categories: list[str] = []
    recorded_at: Optional[str] = None


class GrowthPrediction(BaseModel):
    id: Optional[str] = None
    channel: str
    metric: str  # "followers", "avg_viewers", "subscribers"
    current_value: float = 0.0
    predicted_value: float = 0.0
    predicted_date: str = ""
    confidence: float = 0.0
    trend: str = "stable"  # "rising", "stable", "declining"
    created_at: Optional[str] = None


class GrowthComparison(BaseModel):
    id: Optional[str] = None
    channel: str
    compared_channel: str
    similarity_score: float = 0.0
    growth_phase: str = ""  # "early", "growth", "established", "viral"
    insight: str = ""
    created_at: Optional[str] = None


class StreamerStockEntry(BaseModel):
    channel: str
    stock_score: float = 0.0
    trend: str = "stable"
    change_pct: float = 0.0
    rank: int = 0
    avg_viewers: float = 0.0
    follower_count: int = 0


class AnalyticsOverview(BaseModel):
    channel: str
    growth_score: float = 0.0
    sponsorship_readiness: float = 0.0
    consistency_score: float = 0.0
    engagement_rate: float = 0.0
    trend: str = "stable"
    predictions: list[GrowthPrediction] = []
    comparisons: list[GrowthComparison] = []
    recent_snapshots: list[StreamerSnapshot] = []


class SnapshotCreate(BaseModel):
    channel: str
    avg_viewers: float = 0.0
    peak_viewers: int = 0
    follower_count: int = 0
    subscriber_count: int = 0
    hours_streamed: float = 0.0
    chat_messages: int = 0
    categories: list[str] = []
