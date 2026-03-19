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


# ========== Creator Economy Marketplace ==========
class SellerProfileCreate(BaseModel):
    display_name: str
    bio: str = ""
    avatar_url: Optional[str] = None
    website: Optional[str] = None


class SellerProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    website: Optional[str] = None


class SellerProfile(BaseModel):
    id: Optional[str] = None
    user_id: str
    display_name: str
    bio: str = ""
    avatar_url: Optional[str] = None
    website: Optional[str] = None
    total_sales: int = 0
    total_revenue: float = 0.0
    rating_avg: float = 0.0
    rating_count: int = 0
    status: str = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MarketplaceItemCreate(BaseModel):
    title: str
    description: str = ""
    category: str = "overlay"  # "overlay", "alert_pack", "widget_skin", "chatbot_preset"
    price: float = 0.0
    preview_url: Optional[str] = None
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: list[str] = []


class MarketplaceItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    preview_url: Optional[str] = None
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: Optional[list[str]] = None
    status: Optional[str] = None


class MarketplaceItem(BaseModel):
    id: Optional[str] = None
    seller_id: str
    title: str
    description: str = ""
    category: str = "overlay"
    price: float = 0.0
    currency: str = "USD"
    preview_url: Optional[str] = None
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: list[str] = []
    status: str = "draft"
    download_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MarketplacePurchase(BaseModel):
    id: Optional[str] = None
    item_id: str
    buyer_user_id: str
    seller_id: str
    price_paid: float = 0.0
    platform_fee: float = 0.0
    seller_payout: float = 0.0
    status: str = "completed"
    payment_reference: Optional[str] = None
    created_at: Optional[str] = None


class MarketplaceReviewCreate(BaseModel):
    rating: int = 5  # 1-5
    comment: str = ""


class MarketplaceReview(BaseModel):
    id: Optional[str] = None
    item_id: str
    user_id: str
    rating: int = 5
    comment: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SellerPayout(BaseModel):
    id: Optional[str] = None
    seller_id: str
    amount: float = 0.0
    currency: str = "USD"
    status: str = "pending"  # "pending", "processing", "completed", "failed"
    payment_method: str = "stripe"
    payment_reference: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    created_at: Optional[str] = None
    paid_at: Optional[str] = None


class SellerRevenueAnalytics(BaseModel):
    seller_id: str
    total_revenue: float = 0.0
    total_sales: int = 0
    platform_fees: float = 0.0
    net_revenue: float = 0.0
    pending_payout: float = 0.0
    items_listed: int = 0
    avg_item_rating: float = 0.0
    monthly_revenue: list[dict] = []
    top_items: list[dict] = []


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


# ========== Timed Messages ==========
class TimedMessage(BaseModel):
    id: Optional[str] = None
    channel: str
    message: str
    interval_minutes: int = 15
    enabled: bool = True
    last_sent_at: Optional[str] = None
    created_at: Optional[str] = None


class TimedMessageCreate(BaseModel):
    message: str
    interval_minutes: int = 15
    enabled: bool = True


class TimedMessageUpdate(BaseModel):
    message: Optional[str] = None
    interval_minutes: Optional[int] = None
    enabled: Optional[bool] = None


# ========== Chat Polls & Voting ==========
class PollCreate(BaseModel):
    title: str
    options: list[str]
    duration_seconds: int = 300
    poll_type: str = "standard"  # "standard", "game_map_vote", "color_palette"


class PollVote(BaseModel):
    username: str
    option_index: int


class Poll(BaseModel):
    id: Optional[str] = None
    channel: str
    title: str
    options: list[str] = []
    votes: dict = {}  # {"option_index": count}
    voters: list[str] = []
    poll_type: str = "standard"
    status: str = "active"  # "active", "closed"
    duration_seconds: int = 300
    created_at: Optional[str] = None
    closed_at: Optional[str] = None


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
    winning_outcome_index: int


class Prediction(BaseModel):
    id: Optional[str] = None
    channel: str
    title: str
    outcomes: list[str] = []
    outcome_pools: dict = {}  # {"0": total_points, "1": total_points}
    bets: list[dict] = []
    status: str = "open"  # "open", "locked", "resolved", "cancelled"
    winning_outcome_index: Optional[int] = None
    lock_seconds: int = 300
    created_at: Optional[str] = None
    locked_at: Optional[str] = None
    resolved_at: Optional[str] = None


# ========== Multi-Language Chat Translation ==========
class TranslationSettings(BaseModel):
    channel: str
    enabled: bool = False
    target_language: str = "en"
    auto_translate: bool = False
    updated_at: Optional[str] = None


class TranslationSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    target_language: Optional[str] = None
    auto_translate: Optional[bool] = None


class TranslationRequest(BaseModel):
    text: str
    target_language: str = "en"
    source_language: Optional[str] = None


class TranslationResult(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str


# ========== Game Queue System ==========
class GameQueueCreate(BaseModel):
    game: str = ""
    max_size: int = 20


class GameQueueEntry(BaseModel):
    username: str
    note: str = ""


class GameQueue(BaseModel):
    id: Optional[str] = None
    channel: str
    game: str = ""
    status: str = "open"  # "open", "closed", "in_progress"
    max_size: int = 20
    entries: list[dict] = []
    created_at: Optional[str] = None


class TeamPickResult(BaseModel):
    teams: list[list[str]] = []
    team_size: int = 2


# ========== Match History Tracker ==========
class MatchRecordCreate(BaseModel):
    game: str
    opponent: str = ""
    result: str  # "win", "loss", "draw"
    score: str = ""
    notes: str = ""


class MatchRecord(BaseModel):
    id: Optional[str] = None
    channel: str
    game: str
    opponent: str = ""
    result: str  # "win", "loss", "draw"
    score: str = ""
    notes: str = ""
    played_at: Optional[str] = None


class MatchStats(BaseModel):
    channel: str
    total_matches: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    win_rate: float = 0.0
    current_streak: int = 0
    streak_type: str = ""  # "win", "loss"
    by_game: list[dict] = []


# ========== Kill/Death Counter ==========
class KDCounter(BaseModel):
    id: Optional[str] = None
    channel: str
    game: str = ""
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    session_id: Optional[str] = None
    updated_at: Optional[str] = None


class KDCounterUpdate(BaseModel):
    kills: Optional[int] = None
    deaths: Optional[int] = None
    assists: Optional[int] = None
    game: Optional[str] = None


# ========== Achievement Tracker ==========
class AchievementCreate(BaseModel):
    game: str = ""
    title: str
    description: str = ""
    icon: str = "trophy"


class Achievement(BaseModel):
    id: Optional[str] = None
    channel: str
    game: str = ""
    title: str
    description: str = ""
    icon: str = "trophy"
    unlocked: bool = False
    unlocked_at: Optional[str] = None
    created_at: Optional[str] = None


# ========== Game Challenge System ==========
class GameChallengeCreate(BaseModel):
    title: str
    description: str = ""
    reward_points: int = 0
    creator_username: str = ""


class GameChallenge(BaseModel):
    id: Optional[str] = None
    channel: str
    creator_username: str = ""
    title: str
    description: str = ""
    reward_points: int = 0
    status: str = "pending"  # "pending", "accepted", "completed", "failed", "rejected"
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


# ========== Rank Tracker ==========
class RankTrackerUpdate(BaseModel):
    game: str
    current_rank: str
    rank_points: int = 0
    peak_rank: Optional[str] = None


class RankTracker(BaseModel):
    id: Optional[str] = None
    channel: str
    game: str
    current_rank: str = ""
    peak_rank: str = ""
    rank_points: int = 0
    updated_at: Optional[str] = None


# ========== Slot Request Queue (Gambling) ==========
class SlotRequestCreate(BaseModel):
    username: str
    slot_name: str
    note: str = ""


class SlotRequest(BaseModel):
    id: Optional[str] = None
    channel: str
    username: str
    slot_name: str
    note: str = ""
    status: str = "pending"  # "pending", "playing", "played", "rejected"
    position: int = 0
    created_at: Optional[str] = None


class BannedSlot(BaseModel):
    id: Optional[str] = None
    channel: str
    slot_name: str
    reason: str = ""
    added_at: Optional[str] = None


class BannedSlotCreate(BaseModel):
    slot_name: str
    reason: str = ""


# ========== Gambling Session Tracker ==========
class GamblingSessionCreate(BaseModel):
    start_balance: float = 0.0


class GamblingSession(BaseModel):
    id: Optional[str] = None
    channel: str
    start_balance: float = 0.0
    current_balance: float = 0.0
    total_wagered: float = 0.0
    total_won: float = 0.0
    biggest_win: float = 0.0
    biggest_loss: float = 0.0
    status: str = "active"  # "active", "ended"
    started_at: Optional[str] = None
    ended_at: Optional[str] = None


class GamblingSessionUpdate(BaseModel):
    current_balance: Optional[float] = None
    status: Optional[str] = None


class BetLogCreate(BaseModel):
    slot_name: str = ""
    bet_amount: float
    win_amount: float = 0.0
    result: str = "loss"  # "win", "loss"


class BetLogEntry(BaseModel):
    id: Optional[str] = None
    channel: str
    session_id: str
    slot_name: str = ""
    bet_amount: float = 0.0
    win_amount: float = 0.0
    result: str = "loss"
    running_total: float = 0.0
    created_at: Optional[str] = None


class SlotRatingCreate(BaseModel):
    username: str
    slot_name: str
    rating: int = 5
    comment: str = ""


class SlotRating(BaseModel):
    id: Optional[str] = None
    channel: str
    username: str
    slot_name: str
    rating: int = 5
    comment: str = ""
    created_at: Optional[str] = None


class BalanceMilestone(BaseModel):
    id: Optional[str] = None
    channel: str
    amount: float
    direction: str = "up"  # "up", "down"
    triggered_at: Optional[str] = None


class RainEvent(BaseModel):
    id: Optional[str] = None
    channel: str
    amount: float = 0.0
    currency: str = "USD"
    source: str = ""
    tip_count: int = 0
    created_at: Optional[str] = None


class RainEventCreate(BaseModel):
    amount: float
    currency: str = "USD"
    source: str = ""
    tip_count: int = 0


# ========== IRL Features ==========
class StreamerLocationUpdate(BaseModel):
    city: str = ""
    country: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class StreamerLocation(BaseModel):
    channel: str
    city: str = ""
    country: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    updated_at: Optional[str] = None


class DonationGoalCreate(BaseModel):
    title: str
    target_amount: float
    currency: str = "USD"


class DonationGoal(BaseModel):
    id: Optional[str] = None
    channel: str
    title: str
    target_amount: float = 0.0
    current_amount: float = 0.0
    currency: str = "USD"
    status: str = "active"  # "active", "completed", "cancelled"
    created_at: Optional[str] = None


class DonationGoalUpdate(BaseModel):
    current_amount: Optional[float] = None
    status: Optional[str] = None
    title: Optional[str] = None


class QuestionCreate(BaseModel):
    username: str
    question: str
    priority: int = 0


class Question(BaseModel):
    id: Optional[str] = None
    channel: str
    username: str
    question: str
    status: str = "pending"  # "pending", "answered", "skipped"
    priority: int = 0
    created_at: Optional[str] = None


class PhotoRequestCreate(BaseModel):
    username: str
    description: str = ""
    tip_amount: float = 0.0


class PhotoRequest(BaseModel):
    id: Optional[str] = None
    channel: str
    username: str
    description: str = ""
    status: str = "pending"  # "pending", "accepted", "completed", "rejected"
    tip_amount: float = 0.0
    created_at: Optional[str] = None


class WheelChallengeCreate(BaseModel):
    username: str = ""
    challenge_text: str


class WheelChallenge(BaseModel):
    id: Optional[str] = None
    channel: str
    username: str = ""
    challenge_text: str
    used: bool = False
    created_at: Optional[str] = None


class CountdownTimer(BaseModel):
    id: Optional[str] = None
    channel: str
    title: str = ""
    end_time: str = ""
    style: str = "default"
    active: bool = True
    created_at: Optional[str] = None


class CountdownTimerCreate(BaseModel):
    title: str = ""
    end_time: str
    style: str = "default"


# ========== Creative/Music Features ==========
class ArtCommissionCreate(BaseModel):
    username: str
    description: str
    reference_url: str = ""
    style: str = ""
    size: str = ""
    price: float = 0.0


class ArtCommission(BaseModel):
    id: Optional[str] = None
    channel: str
    username: str
    description: str
    reference_url: str = ""
    style: str = ""
    size: str = ""
    price: float = 0.0
    status: str = "pending"  # "pending", "accepted", "in_progress", "completed", "rejected"
    created_at: Optional[str] = None


class TutorialRequestCreate(BaseModel):
    username: str
    topic: str


class TutorialRequest(BaseModel):
    id: Optional[str] = None
    channel: str
    username: str
    topic: str
    votes: int = 0
    status: str = "pending"  # "pending", "completed"
    created_at: Optional[str] = None


class CollabRequestCreate(BaseModel):
    requester_username: str
    requester_channel: str = ""
    proposal: str


class CollabRequest(BaseModel):
    id: Optional[str] = None
    channel: str
    requester_username: str
    requester_channel: str = ""
    proposal: str
    status: str = "pending"  # "pending", "accepted", "declined", "completed"
    created_at: Optional[str] = None
