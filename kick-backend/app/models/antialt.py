"""Anti-alt detection and anti-cheat schemas."""

from pydantic import BaseModel
from typing import Optional


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
