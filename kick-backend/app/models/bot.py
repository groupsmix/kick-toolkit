"""Bot, moderation, and chat-related schemas."""

from pydantic import BaseModel
from typing import Optional


# ========== Bot & Moderation ==========
class BotConfig(BaseModel):
    channel: str
    prefix: str = "!"
    enabled: bool = True
    welcome_message: Optional[str] = None
    auto_mod_enabled: bool = True
    welcome_enabled: bool = False
    welcome_new_message: Optional[str] = None
    welcome_returning_message: Optional[str] = None
    welcome_subscriber_message: Optional[str] = None


class BotCommand(BaseModel):
    name: str
    response: str
    cooldown: int = 5
    enabled: bool = True
    mod_only: bool = False


class CommandExecuteRequest(BaseModel):
    command_name: str
    username: str = "viewer"


class CommandExecuteResult(BaseModel):
    command_name: str
    original_response: str
    resolved_response: str


class CommandVariable(BaseModel):
    name: str
    description: str


# ========== Timed Messages ==========
class TimedMessageCreate(BaseModel):
    message: str
    interval_minutes: int = 15
    enabled: bool = True


class TimedMessage(BaseModel):
    id: Optional[str] = None
    channel: str
    message: str
    interval_minutes: int = 15
    enabled: bool = True
    created_at: Optional[str] = None


class TimedMessageUpdate(BaseModel):
    message: Optional[str] = None
    interval_minutes: Optional[int] = None
    enabled: Optional[bool] = None


# ========== Welcome Messages ==========
class WelcomeCheckRequest(BaseModel):
    username: str


class WelcomeCheckResult(BaseModel):
    username: str
    welcome_type: str  # "new", "returning", "subscriber", "none"
    message: Optional[str] = None


# ========== Shoutout ==========
class ShoutoutRequest(BaseModel):
    target_username: str


class ShoutoutResult(BaseModel):
    target_username: str
    message: str
    avatar_url: Optional[str] = None
    is_live: bool = False
    game: Optional[str] = None
    title: Optional[str] = None
    follower_count: int = 0


class ShoutoutConfig(BaseModel):
    channel: str
    shoutout_template: str = "Check out {target} at kick.com/{target}! They were last playing {game}."
    auto_shoutout_raiders: bool = False


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
