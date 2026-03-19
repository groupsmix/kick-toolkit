from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ========== Bot & Moderation ==========
class BotConfig(BaseModel):
    channel: str
    prefix: str = "!"
    enabled: bool = True
    welcome_message: Optional[str] = None
    auto_mod_enabled: bool = True


class BotCommand(BaseModel):
    name: str
    response: str
    cooldown: int = 5
    enabled: bool = True
    mod_only: bool = False


class ModerationRule(BaseModel):
    id: Optional[str] = None
    name: str
    type: str  # "spam", "caps", "links", "banned_words", "ai"
    enabled: bool = True
    action: str = "delete"  # "delete", "timeout", "ban", "warn"
    severity: int = 1
    settings: dict = {}


class ChatMessage(BaseModel):
    username: str
    message: str
    timestamp: Optional[str] = None
    channel: str = ""


class ModerationResult(BaseModel):
    flagged: bool
    reason: Optional[str] = None
    action: Optional[str] = None
    confidence: float = 0.0
    categories: dict[str, bool] = {}
    category_scores: dict[str, float] = {}


# ========== Chat Logs ==========
class ChatLogEntry(BaseModel):
    id: Optional[str] = None
    channel: str
    username: str
    message: str
    timestamp: str
    flagged: bool = False
    flag_reason: Optional[str] = None


class ChatLogFilter(BaseModel):
    channel: Optional[str] = None
    username: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    flagged_only: bool = False
    search: Optional[str] = None
    limit: int = 100
    offset: int = 0


# ========== Giveaway ==========
class GiveawayCreate(BaseModel):
    title: str
    channel: str
    keyword: str = "!enter"
    duration_seconds: int = 300
    max_entries: Optional[int] = None
    subscriber_only: bool = False
    follower_only: bool = False
    min_account_age_days: int = 0


class GiveawayEntry(BaseModel):
    username: str
    entered_at: Optional[str] = None


class Giveaway(BaseModel):
    id: str
    title: str
    channel: str
    keyword: str
    status: str  # "pending", "active", "rolling", "completed"
    duration_seconds: int
    max_entries: Optional[int] = None
    subscriber_only: bool = False
    follower_only: bool = False
    min_account_age_days: int = 0
    entries: list[GiveawayEntry] = []
    winner: Optional[str] = None
    created_at: str
    ended_at: Optional[str] = None


# ========== Anti-Alt Detection ==========
class AltCheckRequest(BaseModel):
    username: str
    channel: str


class AutoVerifyRequest(BaseModel):
    username: str
    channel: str
    message: str
    client_ip: Optional[str] = None
    fingerprint: Optional[str] = None
    user_agent: Optional[str] = None


class AutoVerifyResult(BaseModel):
    action: str  # "allow", "challenge", "timeout", "ban"
    risk_score: float
    flags: list[str] = []
    challenge_type: Optional[str] = None
    challenge_message: Optional[str] = None


class AltCheckResult(BaseModel):
    username: str
    risk_score: float  # 0-100
    risk_level: str  # "low", "medium", "high", "critical"
    flags: list[str] = []
    account_age_days: int = 0
    follower_count: int = 0
    is_following: bool = False
    similar_names: list[str] = []
    fingerprint_match_count: int = 0
    behavior_similarity_score: float = 0.0
    created_at: Optional[str] = None


class AntiAltSettings(BaseModel):
    enabled: bool = True
    min_account_age_days: int = 7
    auto_ban_threshold: float = 80.0
    auto_timeout_threshold: float = 50.0
    check_name_similarity: bool = True
    check_follow_status: bool = True
    whitelisted_users: list[str] = []
    challenge_enabled: bool = False
    challenge_type: str = "follow"
    challenge_wait_minutes: int = 10
    challenge_message: str = "Please follow the channel and wait {minutes} minutes before chatting."
    auto_whitelist_enabled: bool = True
    auto_whitelist_min_messages: int = 100
    auto_whitelist_min_follow_days: int = 30


class BannedUser(BaseModel):
    username: str
    channel: str
    banned_at: Optional[str] = None
    ban_reason: Optional[str] = None
    ban_source: str = "manual"


class WhitelistedUser(BaseModel):
    username: str
    channel: str
    added_by: Optional[str] = None
    reason: Optional[str] = None
    tier: str = "regular"
    auto_whitelisted: bool = False
    message_count_at_whitelist: int = 0
    created_at: Optional[str] = None


class ChallengeCheck(BaseModel):
    username: str
    channel: str


class ChallengeResult(BaseModel):
    username: str
    channel: str
    challenge_type: str
    challenge_status: str
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    completed_at: Optional[str] = None


class BehaviorProfile(BaseModel):
    username: str
    channel: str
    message_count: int = 0
    avg_msg_length: float = 0.0
    avg_typing_speed: float = 0.0
    caps_ratio: float = 0.0
    emoji_frequency: float = 0.0
    emoji_profile: dict = {}
    vocab_fingerprint: dict = {}
    timing_histogram: dict = {}
    msg_length_stats: dict = {}
    updated_at: Optional[str] = None


class RiskModelStats(BaseModel):
    channel: str
    feature_weights: dict = {}
    training_samples: int = 0
    last_trained_at: Optional[str] = None
    model_version: int = 1


# ========== Anti-Cheat ==========
class RaidEvent(BaseModel):
    id: Optional[int] = None
    channel: str
    detected_at: Optional[str] = None
    severity: str = "low"
    new_chatters_count: int = 0
    window_seconds: int = 60
    suspicious_accounts: list[str] = []
    auto_action_taken: str = "none"
    resolved: bool = False
    resolved_at: Optional[str] = None


class RaidSettings(BaseModel):
    enabled: bool = True
    new_chatter_threshold: int = 20
    window_seconds: int = 60
    auto_action: str = "none"
    min_account_age_days: int = 7


class GiveawayFraudFlag(BaseModel):
    id: Optional[int] = None
    giveaway_id: str
    username: str
    flag_type: str
    matched_username: Optional[str] = None
    confidence: float = 0.0
    reviewed: bool = False
    review_action: Optional[str] = None
    created_at: Optional[str] = None


class FraudReviewRequest(BaseModel):
    flag_id: int
    action: str  # "allow", "remove"


# ========== Tournament ==========
class TournamentCreate(BaseModel):
    name: str
    channel: str
    game: str = ""
    max_participants: int = 16
    format: str = "single_elimination"  # "single_elimination", "double_elimination", "round_robin"
    keyword: str = "!join"
    entry_duration_seconds: int = 300
    description: str = ""


class TournamentParticipant(BaseModel):
    username: str
    seed: Optional[int] = None
    eliminated: bool = False


class TournamentMatch(BaseModel):
    id: str
    round: int
    match_number: int
    player1: Optional[str] = None
    player2: Optional[str] = None
    winner: Optional[str] = None
    status: str = "pending"  # "pending", "in_progress", "completed"


class Tournament(BaseModel):
    id: str
    name: str
    channel: str
    game: str
    max_participants: int
    format: str
    keyword: str
    status: str  # "registration", "in_progress", "completed"
    participants: list[TournamentParticipant] = []
    matches: list[TournamentMatch] = []
    current_round: int = 1
    winner: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None


# ========== Stream Giveaway Ideas ==========
class GiveawayIdea(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    category: str  # "physical", "digital", "experience", "in-game", "subscription"
    estimated_cost: str = "Free"
    engagement_level: str = "medium"  # "low", "medium", "high"
    requirements: list[str] = []
    saved: bool = False


class IdeaGenerateRequest(BaseModel):
    category: Optional[str] = None
    budget: Optional[str] = None
    audience_size: Optional[str] = None
    game: Optional[str] = None


# ========== Subscriptions ==========
class SubscriptionPlan(BaseModel):
    id: str  # "free", "pro", "premium"
    name: str
    price: float
    currency: str = "USD"
    interval: str = "month"
    features: list[str] = []
    limits: dict[str, int] = {}


class Subscription(BaseModel):
    id: str
    user_id: str
    plan: str = "free"  # "free", "pro", "premium"
    status: str = "active"  # "active", "cancelled", "past_due", "expired"
    lemon_subscription_id: Optional[str] = None
    lemon_customer_id: Optional[str] = None
    lemon_order_id: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class CheckoutRequest(BaseModel):
    plan: str  # "pro" or "premium"


class CheckoutResponse(BaseModel):
    checkout_url: str


class SubscriptionUsage(BaseModel):
    plan: str
    plan_name: str
    status: str
    limits: dict[str, int]
    usage: dict[str, int]


# ========== Predictive Analytics ==========
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


# ========== AI Stream Coach ==========
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


# ========== AI Clip Pipeline ==========
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


# ========== Viewer Heatmap ==========
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


# ========== White-Label Platform ==========
class OrganizationCreate(BaseModel):
    name: str
    slug: str
    plan: str = "starter"
    max_members: int = 5
    custom_domain: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None
    max_members: Optional[int] = None
    custom_domain: Optional[str] = None
    status: Optional[str] = None


class Organization(BaseModel):
    id: Optional[str] = None
    name: str
    slug: str
    owner_user_id: str
    plan: str = "starter"
    status: str = "active"
    max_members: int = 5
    custom_domain: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class OrgMemberAdd(BaseModel):
    user_id: str
    username: str
    role: str = "viewer"  # "admin", "manager", "viewer"
    channel: Optional[str] = None


class OrgMember(BaseModel):
    id: Optional[str] = None
    org_id: str
    user_id: str
    username: str
    role: str = "viewer"
    channel: Optional[str] = None
    joined_at: Optional[str] = None


class OrgBrandingUpdate(BaseModel):
    logo_url: Optional[str] = None
    primary_color: str = "#10b981"
    secondary_color: str = "#6366f1"
    accent_color: str = "#f59e0b"
    dark_mode: bool = True
    custom_css: Optional[str] = None
    welcome_message: Optional[str] = None


class OrgBranding(BaseModel):
    org_id: str
    logo_url: Optional[str] = None
    primary_color: str = "#10b981"
    secondary_color: str = "#6366f1"
    accent_color: str = "#f59e0b"
    dark_mode: bool = True
    custom_css: Optional[str] = None
    welcome_message: Optional[str] = None
    updated_at: Optional[str] = None


class OrgSettingsUpdate(BaseModel):
    features_enabled: list[str] = ["coach", "analytics", "clips", "heatmap"]
    default_role: str = "viewer"
    require_approval: bool = False
    billing_email: Optional[str] = None


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
