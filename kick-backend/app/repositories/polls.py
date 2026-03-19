"""Repository for chat polls & voting."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def list_polls(channel: str, status: Optional[str] = None) -> list[dict]:
    async with get_conn() as conn:
        if status:
            row = await conn.execute(
                "SELECT * FROM polls WHERE channel = %s AND status = %s ORDER BY created_at DESC",
                (channel, status),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM polls WHERE channel = %s ORDER BY created_at DESC",
                (channel,),
            )
        results = await row.fetchall()
    out = []
    for r in results:
        d = dict(r)
        for key in ("options", "voters"):
            if isinstance(d.get(key), str):
                d[key] = json.loads(d[key])
        if isinstance(d.get("votes"), str):
            d["votes"] = json.loads(d["votes"])
        out.append(d)
    return out


async def create_poll(channel: str, title: str, options: list[str], duration_seconds: int, poll_type: str) -> dict:
    poll_id = _generate_id()
    now = _now_iso()
    votes = {str(i): 0 for i in range(len(options))}
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO polls (id, channel, title, options, votes, voters, poll_type, status, duration_seconds, created_at)
               VALUES (%s, %s, %s, %s, %s, '[]', %s, 'active', %s, %s)""",
            (poll_id, channel, title, json.dumps(options), json.dumps(votes), poll_type, duration_seconds, now),
        )
        await conn.commit()
    return {
        "id": poll_id, "channel": channel, "title": title, "options": options,
        "votes": votes, "voters": [], "poll_type": poll_type, "status": "active",
        "duration_seconds": duration_seconds, "created_at": now,
    }


async def vote(channel: str, poll_id: str, username: str, option_index: int) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM polls WHERE id = %s AND channel = %s AND status = 'active'",
            (poll_id, channel),
        )
        poll = await row.fetchone()
        if not poll:
            return None

        voters = json.loads(poll["voters"]) if isinstance(poll["voters"], str) else poll["voters"]
        if username in voters:
            return None

        votes = json.loads(poll["votes"]) if isinstance(poll["votes"], str) else poll["votes"]
        key = str(option_index)
        votes[key] = votes.get(key, 0) + 1
        voters.append(username)

        await conn.execute(
            "UPDATE polls SET votes = %s, voters = %s WHERE id = %s AND channel = %s",
            (json.dumps(votes), json.dumps(voters), poll_id, channel),
        )
        await conn.commit()

    options = json.loads(poll["options"]) if isinstance(poll["options"], str) else poll["options"]
    return {
        "id": poll_id, "channel": channel, "title": poll["title"], "options": options,
        "votes": votes, "voters": voters, "poll_type": poll["poll_type"],
        "status": "active", "duration_seconds": poll["duration_seconds"],
        "created_at": poll["created_at"],
    }


async def close_poll(channel: str, poll_id: str) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM polls WHERE id = %s AND channel = %s",
            (poll_id, channel),
        )
        poll = await row.fetchone()
        if not poll:
            return None

        await conn.execute(
            "UPDATE polls SET status = 'closed', closed_at = %s WHERE id = %s AND channel = %s",
            (now, poll_id, channel),
        )
        await conn.commit()

    d = dict(poll)
    d["status"] = "closed"
    d["closed_at"] = now
    for key in ("options", "voters"):
        if isinstance(d.get(key), str):
            d[key] = json.loads(d[key])
    if isinstance(d.get("votes"), str):
        d["votes"] = json.loads(d["votes"])
    return d


async def delete_poll(channel: str, poll_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM polls WHERE id = %s AND channel = %s",
            (poll_id, channel),
        )
        await conn.commit()
