"""Repository for game queue system."""

import json
import random
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def get_queue(channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM game_queues WHERE channel = %s AND status != 'closed' ORDER BY created_at DESC LIMIT 1",
            (channel,),
        )
        result = await row.fetchone()
    if not result:
        return None
    d = dict(result)
    if isinstance(d.get("entries"), str):
        d["entries"] = json.loads(d["entries"])
    return d


async def create_queue(channel: str, game: str, max_size: int) -> dict:
    queue_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO game_queues (id, channel, game, status, max_size, entries, created_at)
               VALUES (%s, %s, %s, 'open', %s, '[]', %s)""",
            (queue_id, channel, game, max_size, now),
        )
        await conn.commit()
    return {
        "id": queue_id, "channel": channel, "game": game, "status": "open",
        "max_size": max_size, "entries": [], "created_at": now,
    }


async def join_queue(channel: str, queue_id: str, username: str, note: str = "") -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM game_queues WHERE id = %s AND channel = %s AND status = 'open'",
            (queue_id, channel),
        )
        queue = await row.fetchone()
        if not queue:
            return None

        entries = json.loads(queue["entries"]) if isinstance(queue["entries"], str) else queue["entries"]
        if len(entries) >= queue["max_size"]:
            return None
        if any(e["username"] == username for e in entries):
            return None

        entries.append({"username": username, "note": note})
        await conn.execute(
            "UPDATE game_queues SET entries = %s WHERE id = %s AND channel = %s",
            (json.dumps(entries), queue_id, channel),
        )
        await conn.commit()

    d = dict(queue)
    d["entries"] = entries
    return d


async def leave_queue(channel: str, queue_id: str, username: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM game_queues WHERE id = %s AND channel = %s",
            (queue_id, channel),
        )
        queue = await row.fetchone()
        if not queue:
            return None

        entries = json.loads(queue["entries"]) if isinstance(queue["entries"], str) else queue["entries"]
        entries = [e for e in entries if e["username"] != username]
        await conn.execute(
            "UPDATE game_queues SET entries = %s WHERE id = %s AND channel = %s",
            (json.dumps(entries), queue_id, channel),
        )
        await conn.commit()

    d = dict(queue)
    d["entries"] = entries
    return d


async def close_queue(channel: str, queue_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE game_queues SET status = 'closed' WHERE id = %s AND channel = %s",
            (queue_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM game_queues WHERE id = %s", (queue_id,))
        result = await row.fetchone()
    if not result:
        return None
    d = dict(result)
    if isinstance(d.get("entries"), str):
        d["entries"] = json.loads(d["entries"])
    return d


async def pick_teams(channel: str, queue_id: str, team_count: int = 2) -> dict:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM game_queues WHERE id = %s AND channel = %s",
            (queue_id, channel),
        )
        queue = await row.fetchone()

    entries = json.loads(queue["entries"]) if isinstance(queue["entries"], str) else queue["entries"]
    usernames = [e["username"] for e in entries]
    random.shuffle(usernames)

    teams: list[list[str]] = [[] for _ in range(team_count)]
    for i, name in enumerate(usernames):
        teams[i % team_count].append(name)

    return {"teams": teams, "team_size": len(usernames) // team_count if team_count else 0}
