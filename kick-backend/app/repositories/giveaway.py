"""Repository for giveaway data access."""

import json
import random
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def list_giveaways(channel: str = "") -> list[dict]:
    async with get_conn() as conn:
        if channel:
            row = await conn.execute(
                "SELECT * FROM giveaways WHERE channel = %s ORDER BY created_at DESC", (channel,)
            )
        else:
            row = await conn.execute("SELECT * FROM giveaways ORDER BY created_at DESC")
        return [dict(g) for g in await row.fetchall()]


async def create(title: str, channel: str, keyword: str, duration_seconds: int, max_entries: Optional[int], subscriber_only: bool, follower_only: bool, min_account_age_days: int) -> dict:
    gw_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO giveaways (id, title, channel, keyword, status, duration_seconds, max_entries,
               subscriber_only, follower_only, min_account_age_days, entries, winner, created_at, ended_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (gw_id, title, channel, keyword, "active", duration_seconds,
             max_entries, subscriber_only, follower_only, min_account_age_days,
             "[]", None, now, None),
        )
        await conn.commit()
    return {
        "id": gw_id, "title": title, "channel": channel, "keyword": keyword,
        "status": "active", "duration_seconds": duration_seconds,
        "max_entries": max_entries, "subscriber_only": subscriber_only,
        "follower_only": follower_only, "min_account_age_days": min_account_age_days,
        "entries": [], "winner": None, "created_at": now, "ended_at": None,
    }


async def get_by_id(giveaway_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM giveaways WHERE id = %s", (giveaway_id,))
        gw = await row.fetchone()
    return dict(gw) if gw else None


async def add_entry(giveaway_id: str, username: str) -> tuple[dict, int]:
    """Add an entry to a giveaway. Returns (entry_data, total_entries). Raises ValueError on validation failure."""
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM giveaways WHERE id = %s", (giveaway_id,))
        gw = await row.fetchone()

        if not gw:
            raise ValueError("not_found")
        if gw["status"] != "active":
            raise ValueError("not_active")

        entries = gw["entries"] if isinstance(gw["entries"], list) else json.loads(gw["entries"])

        if gw["max_entries"] and len(entries) >= gw["max_entries"]:
            raise ValueError("full")
        if any(e["username"].lower() == username.lower() for e in entries):
            raise ValueError("duplicate")

        entry_data = {"username": username, "entered_at": _now_iso()}
        entries.append(entry_data)

        await conn.execute(
            "UPDATE giveaways SET entries = %s WHERE id = %s",
            (json.dumps(entries), giveaway_id),
        )
        await conn.commit()

    return entry_data, len(entries)


async def roll_winner(giveaway_id: str) -> tuple[str, int, dict]:
    """Roll a winner. Returns (winner_username, total_entries, updated_giveaway). Raises ValueError on validation failure."""
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM giveaways WHERE id = %s", (giveaway_id,))
        gw = await row.fetchone()

        if not gw:
            raise ValueError("not_found")

        entries = gw["entries"] if isinstance(gw["entries"], list) else json.loads(gw["entries"])
        if not entries:
            raise ValueError("no_entries")

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
    return winner["username"], len(entries), gw_dict


async def reroll_winner(giveaway_id: str) -> tuple[str, Optional[str], int]:
    """Reroll a winner. Returns (new_winner, previous_winner, total_entries). Raises ValueError."""
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM giveaways WHERE id = %s", (giveaway_id,))
        gw = await row.fetchone()

        if not gw:
            raise ValueError("not_found")

        entries = gw["entries"] if isinstance(gw["entries"], list) else json.loads(gw["entries"])
        if not entries:
            raise ValueError("no_entries")

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

    return winner["username"], previous_winner, len(entries)


async def close(giveaway_id: str) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        row = await conn.execute(
            "UPDATE giveaways SET status = 'completed', ended_at = %s WHERE id = %s RETURNING *",
            (now, giveaway_id),
        )
        gw = await row.fetchone()
        await conn.commit()
    return dict(gw) if gw else None


async def delete(giveaway_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM giveaways WHERE id = %s", (giveaway_id,))
        await conn.commit()
