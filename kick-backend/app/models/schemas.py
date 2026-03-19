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
