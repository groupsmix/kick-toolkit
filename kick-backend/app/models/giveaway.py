"""Giveaway-related schemas."""

from pydantic import BaseModel
from typing import Optional


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
