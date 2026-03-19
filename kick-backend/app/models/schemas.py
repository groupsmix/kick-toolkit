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


class AltCheckResult(BaseModel):
    username: str
    risk_score: float  # 0-100
    risk_level: str  # "low", "medium", "high", "critical"
    flags: list[str] = []
    account_age_days: int = 0
    follower_count: int = 0
    is_following: bool = False
    similar_names: list[str] = []
    created_at: Optional[str] = None


class AntiAltSettings(BaseModel):
    enabled: bool = True
    min_account_age_days: int = 7
    auto_ban_threshold: float = 80.0
    auto_timeout_threshold: float = 50.0
    check_name_similarity: bool = True
    check_follow_status: bool = True
    whitelisted_users: list[str] = []


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
