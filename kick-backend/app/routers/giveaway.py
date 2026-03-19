"""Giveaway system router."""

import json
import random

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth
from app.models.schemas import GiveawayCreate, GiveawayEntry
from app.services.db import get_conn, _generate_id, _now_iso

router = APIRouter(prefix="/api/giveaway", tags=["giveaway"])


@router.get("")
async def list_giveaways(channel: str = "", _session: dict = Depends(require_auth)) -> list[dict]:
    async with get_conn() as conn:
        if channel:
            row = await conn.execute(
                "SELECT * FROM giveaways WHERE channel = %s ORDER BY created_at DESC", (channel,)
            )
        else:
            row = await conn.execute("SELECT * FROM giveaways ORDER BY created_at DESC")
        giveaways = await row.fetchall()
    return [dict(g) for g in giveaways]


@router.post("/create")
async def create_giveaway(data: GiveawayCreate, _session: dict = Depends(require_auth)) -> dict:
    gw_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO giveaways (id, title, channel, keyword, status, duration_seconds, max_entries,
               subscriber_only, follower_only, min_account_age_days, entries, winner, created_at, ended_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (gw_id, data.title, data.channel, data.keyword, "active", data.duration_seconds,
             data.max_entries, data.subscriber_only, data.follower_only, data.min_account_age_days,
             "[]", None, now, None),
        )
        await conn.commit()
    return {
        "id": gw_id, **data.model_dump(), "status": "active",
        "entries": [], "winner": None, "created_at": now, "ended_at": None,
    }


@router.get("/{giveaway_id}")
async def get_giveaway(giveaway_id: str, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM giveaways WHERE id = %s", (giveaway_id,))
        gw = await row.fetchone()
    if not gw:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    return dict(gw)


@router.post("/{giveaway_id}/enter")
async def enter_giveaway(giveaway_id: str, entry: GiveawayEntry, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM giveaways WHERE id = %s", (giveaway_id,))
        gw = await row.fetchone()

        if not gw:
            raise HTTPException(status_code=404, detail="Giveaway not found")
        if gw["status"] != "active":
            raise HTTPException(status_code=400, detail="Giveaway is not active")

        entries = gw["entries"] if isinstance(gw["entries"], list) else json.loads(gw["entries"])

        if gw["max_entries"] and len(entries) >= gw["max_entries"]:
            raise HTTPException(status_code=400, detail="Giveaway is full")

        if any(e["username"].lower() == entry.username.lower() for e in entries):
            raise HTTPException(status_code=409, detail="Already entered")

        entry_data = {"username": entry.username, "entered_at": _now_iso()}
        entries.append(entry_data)

        await conn.execute(
            "UPDATE giveaways SET entries = %s WHERE id = %s",
            (json.dumps(entries), giveaway_id),
        )
        await conn.commit()

    return {"status": "entered", "entry": entry_data, "total_entries": len(entries)}


@router.post("/{giveaway_id}/roll")
async def roll_giveaway(giveaway_id: str, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM giveaways WHERE id = %s", (giveaway_id,))
        gw = await row.fetchone()

        if not gw:
            raise HTTPException(status_code=404, detail="Giveaway not found")

        entries = gw["entries"] if isinstance(gw["entries"], list) else json.loads(gw["entries"])
        if not entries:
            raise HTTPException(status_code=400, detail="No entries to roll from")

        winner = random.choice(entries)
        now = _now_iso()
        await conn.execute(
            "UPDATE giveaways SET winner = %s, status = 'completed', ended_at = %s WHERE id = %s",
            (winner["username"], now, giveaway_id),
        )
        await conn.commit()

    gw_dict = dict(gw)
    gw_dict["winner"] = winner["username"]
    gw_dict["status"] = "completed"
    gw_dict["ended_at"] = now
    return {"winner": winner["username"], "total_entries": len(entries), "giveaway": gw_dict}


@router.post("/{giveaway_id}/reroll")
async def reroll_giveaway(giveaway_id: str, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM giveaways WHERE id = %s", (giveaway_id,))
        gw = await row.fetchone()

        if not gw:
            raise HTTPException(status_code=404, detail="Giveaway not found")

        entries = gw["entries"] if isinstance(gw["entries"], list) else json.loads(gw["entries"])
        if not entries:
            raise HTTPException(status_code=400, detail="No entries to roll from")

        previous_winner = gw["winner"]
        eligible = [e for e in entries if e["username"] != previous_winner]
        if not eligible:
            eligible = entries

        winner = random.choice(eligible)
        await conn.execute(
            "UPDATE giveaways SET winner = %s, status = 'completed' WHERE id = %s",
            (winner["username"], giveaway_id),
        )
        await conn.commit()

    return {"winner": winner["username"], "previous_winner": previous_winner, "total_entries": len(entries)}


@router.post("/{giveaway_id}/close")
async def close_giveaway(giveaway_id: str, _session: dict = Depends(require_auth)) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        row = await conn.execute(
            "UPDATE giveaways SET status = 'completed', ended_at = %s WHERE id = %s RETURNING *",
            (now, giveaway_id),
        )
        gw = await row.fetchone()
        await conn.commit()

    if not gw:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    return dict(gw)


@router.delete("/{giveaway_id}")
async def delete_giveaway(giveaway_id: str, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM giveaways WHERE id = %s", (giveaway_id,))
        await conn.commit()
    return {"status": "deleted"}
