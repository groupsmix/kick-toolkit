"""Giveaway system router."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import Giveaway, GiveawayCreate, GiveawayEntry
from app.repositories import giveaway as giveaway_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/giveaway", tags=["giveaway"])


@router.get("")
async def list_giveaways(channel: str, session: dict = Depends(require_auth)) -> list[Giveaway]:
    require_channel_owner(session, channel)
    rows = await giveaway_repo.list_giveaways(channel)
    return [Giveaway(**row) for row in rows]


@router.post("/create")
async def create_giveaway(data: GiveawayCreate, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, data.channel)
    result = await giveaway_repo.create(
        title=data.title, channel=data.channel, keyword=data.keyword,
        duration_seconds=data.duration_seconds, max_entries=data.max_entries,
        subscriber_only=data.subscriber_only, follower_only=data.follower_only,
        min_account_age_days=data.min_account_age_days,
    )
    logger.info("Giveaway '%s' created in channel=%s", data.title, data.channel)
    return result


@router.get("/{giveaway_id}")
async def get_giveaway(giveaway_id: str, session: dict = Depends(require_auth)) -> Giveaway:
    gw = await giveaway_repo.get_by_id(giveaway_id)
    if not gw:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    require_channel_owner(session, gw["channel"])
    return Giveaway(**gw)


@router.post("/{giveaway_id}/enter")
async def enter_giveaway(giveaway_id: str, entry: GiveawayEntry, session: dict = Depends(require_auth)) -> dict:
    gw = await giveaway_repo.get_by_id(giveaway_id)
    if not gw:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    require_channel_owner(session, gw["channel"])
    try:
        entry_data, total = await giveaway_repo.add_entry(giveaway_id, entry.username)
    except ValueError as e:
        error_map = {
            "not_found": (404, "Giveaway not found"),
            "not_active": (400, "Giveaway is not active"),
            "full": (400, "Giveaway is full"),
            "duplicate": (409, "Already entered"),
        }
        status, detail = error_map.get(str(e), (400, str(e)))
        raise HTTPException(status_code=status, detail=detail)
    return {"status": "entered", "entry": entry_data, "total_entries": total}


@router.post("/{giveaway_id}/roll")
async def roll_giveaway(giveaway_id: str, session: dict = Depends(require_auth)) -> dict:
    # Verify ownership by looking up the giveaway's channel
    gw = await giveaway_repo.get_by_id(giveaway_id)
    if not gw:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    require_channel_owner(session, gw["channel"])
    try:
        winner, total, gw_dict = await giveaway_repo.roll_winner(giveaway_id)
    except ValueError as e:
        error_map = {
            "not_found": (404, "Giveaway not found"),
            "no_entries": (400, "No entries to roll from"),
        }
        status, detail = error_map.get(str(e), (400, str(e)))
        raise HTTPException(status_code=status, detail=detail)
    logger.info("Giveaway %s winner rolled: %s", giveaway_id, winner)
    return {"winner": winner, "total_entries": total, "giveaway": gw_dict}


@router.post("/{giveaway_id}/reroll")
async def reroll_giveaway(giveaway_id: str, session: dict = Depends(require_auth)) -> dict:
    gw = await giveaway_repo.get_by_id(giveaway_id)
    if not gw:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    require_channel_owner(session, gw["channel"])
    try:
        winner, previous, total = await giveaway_repo.reroll_winner(giveaway_id)
    except ValueError as e:
        error_map = {
            "not_found": (404, "Giveaway not found"),
            "no_entries": (400, "No entries to roll from"),
        }
        status, detail = error_map.get(str(e), (400, str(e)))
        raise HTTPException(status_code=status, detail=detail)
    logger.info("Giveaway %s rerolled: %s -> %s", giveaway_id, previous, winner)
    return {"winner": winner, "previous_winner": previous, "total_entries": total}


@router.post("/{giveaway_id}/close")
async def close_giveaway(giveaway_id: str, session: dict = Depends(require_auth)) -> Giveaway:
    existing = await giveaway_repo.get_by_id(giveaway_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    require_channel_owner(session, existing["channel"])
    gw = await giveaway_repo.close(giveaway_id)
    if not gw:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    return Giveaway(**gw)


@router.delete("/{giveaway_id}")
async def delete_giveaway(giveaway_id: str, session: dict = Depends(require_auth)) -> dict:
    gw = await giveaway_repo.get_by_id(giveaway_id)
    if not gw:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    require_channel_owner(session, gw["channel"])
    await giveaway_repo.delete(giveaway_id)
    logger.info("Giveaway %s deleted", giveaway_id)
    return {"status": "deleted"}
