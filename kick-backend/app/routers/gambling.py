"""Gambling Streamer Features router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import (
    SlotRequestCreate, BannedSlotCreate, GamblingSessionCreate,
    GamblingSessionUpdate, BetLogCreate, SlotRatingCreate, RainEventCreate,
)
from app.repositories import gambling as gamb_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gambling", tags=["gambling"])


# ========== Slot Request Queue ==========
@router.get("/slots/{channel}/requests")
async def list_slot_requests(
    channel: str,
    status: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await gamb_repo.list_slot_requests(channel, status)


@router.post("/slots/{channel}/requests")
async def create_slot_request(
    channel: str, body: SlotRequestCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await gamb_repo.create_slot_request(channel, body.username, body.slot_name, body.note)
    if not result:
        raise HTTPException(status_code=400, detail="Slot is banned or request failed")
    return result


@router.post("/slots/{channel}/requests/{req_id}/status")
async def update_slot_request_status(
    channel: str, req_id: str, status: str = Query(...),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await gamb_repo.update_slot_request_status(channel, req_id, status)
    if not result:
        raise HTTPException(status_code=404, detail="Slot request not found")
    return result


@router.delete("/slots/{channel}/requests/{req_id}")
async def delete_slot_request(
    channel: str, req_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await gamb_repo.delete_slot_request(channel, req_id)
    return {"status": "deleted"}


# ========== Banned Slots ==========
@router.get("/slots/{channel}/banned")
async def list_banned_slots(
    channel: str, _session: dict = Depends(require_auth)
) -> list[dict]:
    return await gamb_repo.list_banned_slots(channel)


@router.post("/slots/{channel}/banned")
async def add_banned_slot(
    channel: str, body: BannedSlotCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await gamb_repo.add_banned_slot(channel, body.slot_name, body.reason)
    logger.info("Slot '%s' banned for channel=%s", body.slot_name, channel)
    return result


@router.delete("/slots/{channel}/banned/{slot_id}")
async def remove_banned_slot(
    channel: str, slot_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await gamb_repo.remove_banned_slot(channel, slot_id)
    return {"status": "deleted"}


# ========== Gambling Sessions ==========
@router.get("/sessions/{channel}")
async def list_sessions(
    channel: str,
    limit: int = Query(default=20, le=100),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await gamb_repo.list_sessions(channel, limit)


@router.get("/sessions/{channel}/active")
async def get_active_session(
    channel: str, _session: dict = Depends(require_auth)
) -> dict:
    session = await gamb_repo.get_active_session(channel)
    if not session:
        return {"channel": channel, "status": "none"}
    return session


@router.post("/sessions/{channel}")
async def create_session(
    channel: str, body: GamblingSessionCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await gamb_repo.create_session(channel, body.start_balance)
    logger.info("Gambling session started for channel=%s balance=%.2f", channel, body.start_balance)
    return result


@router.post("/sessions/{channel}/{session_id}/end")
async def end_session(
    channel: str, session_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await gamb_repo.end_session(channel, session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.post("/sessions/{channel}/{session_id}/update")
async def update_session(
    channel: str, session_id: str, body: GamblingSessionUpdate,
    _session: dict = Depends(require_auth),
) -> dict:
    updates = body.model_dump(exclude_none=True)
    result = await gamb_repo.update_session(channel, session_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


# ========== Bet Log ==========
@router.get("/bets/{channel}/{session_id}")
async def list_bets(
    channel: str, session_id: str,
    limit: int = Query(default=100, le=500),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await gamb_repo.list_bets(channel, session_id, limit)


@router.post("/bets/{channel}/{session_id}")
async def log_bet(
    channel: str, session_id: str, body: BetLogCreate,
    _session: dict = Depends(require_auth),
) -> dict:
    result = await gamb_repo.log_bet(
        channel, session_id, body.slot_name,
        body.bet_amount, body.win_amount, body.result,
    )
    return result


# ========== Slot Ratings ==========
@router.get("/ratings/{channel}")
async def list_slot_ratings(
    channel: str,
    slot_name: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await gamb_repo.list_slot_ratings(channel, slot_name)


@router.post("/ratings/{channel}")
async def rate_slot(
    channel: str, body: SlotRatingCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await gamb_repo.rate_slot(channel, body.username, body.slot_name, body.rating, body.comment)
    return result


# ========== Hot/Cold Slot Stats ==========
@router.get("/slot-stats/{channel}")
async def get_slot_stats(
    channel: str, _session: dict = Depends(require_auth)
) -> list[dict]:
    return await gamb_repo.get_slot_stats(channel)


# ========== Balance Milestones ==========
@router.get("/milestones/{channel}")
async def list_milestones(
    channel: str, _session: dict = Depends(require_auth)
) -> list[dict]:
    return await gamb_repo.list_milestones(channel)


@router.post("/milestones/{channel}")
async def add_milestone(
    channel: str, amount: float = Query(...), direction: str = Query(default="up"),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await gamb_repo.add_milestone(channel, amount, direction)
    return result


# ========== Rain/Tip Tracker ==========
@router.get("/rain/{channel}")
async def list_rain_events(
    channel: str,
    limit: int = Query(default=50, le=200),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await gamb_repo.list_rain_events(channel, limit)


@router.post("/rain/{channel}")
async def create_rain_event(
    channel: str, body: RainEventCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await gamb_repo.create_rain_event(
        channel, body.amount, body.currency, body.source, body.tip_count,
    )
    return result


@router.get("/rain/{channel}/stats")
async def get_rain_stats(
    channel: str, _session: dict = Depends(require_auth)
) -> dict:
    return await gamb_repo.get_rain_stats(channel)
