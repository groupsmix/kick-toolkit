"""Tournament-related schemas."""

from pydantic import BaseModel
from typing import Optional


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
