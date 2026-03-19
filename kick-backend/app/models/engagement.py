"""Engagement feature schemas: loyalty, songs, schedule, overlays, polls, predictions, translation."""

from pydantic import BaseModel
from typing import Optional


# ========== Loyalty & Points System ==========
class LoyaltySettings(BaseModel):
    channel: str
    enabled: bool = True
    points_name: str = "Points"
    points_per_message: int = 1
    points_per_minute_watched: int = 2
    bonus_subscriber_multiplier: float = 2.0
    bonus_follower_multiplier: float = 1.5
    daily_bonus: int = 50
    updated_at: Optional[str] = None


class LoyaltySettingsUpdate(BaseModel):
    enabled: bool = True
    points_name: str = "Points"
    points_per_message: int = 1
    points_per_minute_watched: int = 2
    bonus_subscriber_multiplier: float = 2.0
    bonus_follower_multiplier: float = 1.5
    daily_bonus: int = 50


class LoyaltyPoints(BaseModel):
    username: str
    channel: str
    balance: int = 0
    total_earned: int = 0
    total_spent: int = 0
    watch_time_minutes: int = 0
    message_count: int = 0
    last_daily_bonus: Optional[str] = None
    updated_at: Optional[str] = None


class LoyaltyReward(BaseModel):
    id: Optional[str] = None
    channel: str
    name: str
    description: str = ""
    cost: int = 100
    type: str = "custom"  # "vip", "shoutout", "custom_command", "custom"
    enabled: bool = True
    max_redemptions: Optional[int] = None
    total_redemptions: int = 0
    created_at: Optional[str] = None


class LoyaltyRewardCreate(BaseModel):
    name: str
    description: str = ""
    cost: int = 100
    type: str = "custom"
    enabled: bool = True
    max_redemptions: Optional[int] = None


class LoyaltyRedemption(BaseModel):
    id: Optional[str] = None
    channel: str
    username: str
    reward_id: str
    reward_name: str
    cost: int
    status: str = "pending"  # "pending", "fulfilled", "rejected"
    created_at: Optional[str] = None


class LoyaltyRedeemRequest(BaseModel):
    username: str
    reward_id: str


class PointsAdjustRequest(BaseModel):
    username: str
    amount: int
    reason: str = ""


# ========== Song Request System ==========
class SongQueueSettings(BaseModel):
    channel: str
    enabled: bool = True
    max_queue_size: int = 50
    max_duration_seconds: int = 600
    allow_duplicates: bool = False
    subscriber_only: bool = False
    cost_per_request: int = 0
    updated_at: Optional[str] = None


class SongQueueSettingsUpdate(BaseModel):
    enabled: bool = True
    max_queue_size: int = 50
    max_duration_seconds: int = 600
    allow_duplicates: bool = False
    subscriber_only: bool = False
    cost_per_request: int = 0


class SongRequest(BaseModel):
    id: Optional[str] = None
    channel: str
    username: str
    title: str
    artist: str = ""
    url: Optional[str] = None
    platform: str = "youtube"  # "youtube", "spotify"
    duration_seconds: int = 0
    status: str = "queued"  # "queued", "playing", "played", "skipped"
    position: int = 0
    created_at: Optional[str] = None


class SongRequestCreate(BaseModel):
    username: str
    title: str
    artist: str = ""
    url: Optional[str] = None
    platform: str = "youtube"
    duration_seconds: int = 0


# ========== Stream Schedule ==========
class ScheduleEntry(BaseModel):
    id: Optional[str] = None
    channel: str
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str  # "HH:MM" in UTC
    end_time: str  # "HH:MM" in UTC
    title: str = ""
    game: str = ""
    recurring: bool = True
    enabled: bool = True
    created_at: Optional[str] = None


class ScheduleEntryCreate(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    title: str = ""
    game: str = ""
    recurring: bool = True
    enabled: bool = True


class ScheduleEntryUpdate(BaseModel):
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    title: Optional[str] = None
    game: Optional[str] = None
    recurring: Optional[bool] = None
    enabled: Optional[bool] = None


# ========== Public Streamer Profile ==========
class StreamerProfile(BaseModel):
    channel: str
    display_name: str = ""
    bio: str = ""
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    social_links: dict = {}  # {"twitter": "...", "discord": "...", "youtube": "..."}
    is_public: bool = True
    theme_color: str = "#10b981"
    total_followers: int = 0
    updated_at: Optional[str] = None


class StreamerProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    social_links: Optional[dict] = None
    is_public: Optional[bool] = None
    theme_color: Optional[str] = None


# ========== OBS Overlay Widgets ==========
class OverlaySettings(BaseModel):
    id: Optional[str] = None
    channel: str
    overlay_type: str  # "chat", "alerts", "giveaway", "nowplaying"
    enabled: bool = True
    token: str = ""
    config: dict = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class OverlaySettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[dict] = None


# ========== Chat Polls & Voting ==========
class PollCreate(BaseModel):
    title: str
    options: list[str]
    duration_seconds: int = 300
    allow_multiple_votes: bool = False


class PollVote(BaseModel):
    username: str
    option_index: int


class Poll(BaseModel):
    id: Optional[str] = None
    channel: str
    title: str
    options: list[str] = []
    duration_seconds: int = 300
    allow_multiple_votes: bool = False
    status: str = "active"  # "active", "closed"
    created_at: Optional[str] = None
    closed_at: Optional[str] = None


class PollResult(BaseModel):
    option: str
    index: int
    votes: int = 0
    percentage: float = 0.0


# ========== Predictions System ==========
class PredictionCreate(BaseModel):
    title: str
    outcomes: list[str]
    lock_seconds: int = 300


class PredictionBet(BaseModel):
    username: str
    outcome_index: int
    amount: int


class PredictionResolve(BaseModel):
    winning_index: int


class Prediction(BaseModel):
    id: Optional[str] = None
    channel: str
    title: str
    outcomes: list[str] = []
    lock_seconds: int = 300
    status: str = "open"  # "open", "locked", "resolved", "cancelled"
    winning_index: Optional[int] = None
    created_at: Optional[str] = None
    locked_at: Optional[str] = None
    resolved_at: Optional[str] = None


class PredictionBetRecord(BaseModel):
    id: Optional[str] = None
    prediction_id: str
    channel: str
    username: str
    outcome_index: int
    amount: int = 0
    status: str = "pending"  # "pending", "won", "lost", "refunded"
    payout: int = 0
    created_at: Optional[str] = None


# ========== Multi-Language Chat Translation ==========
class TranslationRequest(BaseModel):
    text: str
    target_language: str = "en"
    source_language: Optional[str] = None


class TranslationResult(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    was_translated: bool = False


class TranslationSettingsUpdate(BaseModel):
    enabled: bool = False
    target_language: str = "en"
    auto_translate: bool = False
    show_original: bool = True


class TranslationSettings(BaseModel):
    channel: str
    enabled: bool = False
    target_language: str = "en"
    auto_translate: bool = False
    show_original: bool = True
    updated_at: Optional[str] = None
