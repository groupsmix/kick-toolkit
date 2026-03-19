"""Repository for chat polls and voting."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def create_poll(
    channel: str, title: str, options: list[str],
    duration_seconds: int, allow_multiple_votes: bool,
) -> dict:
    poll_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO polls
               (id, channel, title, options, duration_seconds, allow_multiple_votes,
                status, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, 'active', %s)""",
            (poll_id, channel, title, json.dumps(options), duration_seconds,
             allow_multiple_votes, now),
        )
        await conn.commit()
    return {
        "id": poll_id, "channel": channel, "title": title, "options": options,
        "duration_seconds": duration_seconds,
        "allow_multiple_votes": allow_multiple_votes,
        "status": "active", "created_at": now,
    }


async def list_polls(channel: str, limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM polls WHERE channel = %s
               ORDER BY created_at DESC LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def get_poll(channel: str, poll_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM polls WHERE id = %s AND channel = %s",
            (poll_id, channel),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def cast_vote(
    channel: str, poll_id: str, username: str, option_index: int,
) -> Optional[dict]:
    vote_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        # Check poll exists and is active
        row = await conn.execute(
            "SELECT * FROM polls WHERE id = %s AND channel = %s AND status = 'active'",
            (poll_id, channel),
        )
        poll = await row.fetchone()
        if not poll:
            return None

        poll = dict(poll)
        options = poll["options"] if isinstance(poll["options"], list) else json.loads(poll["options"])
        if option_index < 0 or option_index >= len(options):
            return None

        # Check if already voted (unless multiple votes allowed)
        if not poll["allow_multiple_votes"]:
            row = await conn.execute(
                "SELECT id FROM poll_votes WHERE poll_id = %s AND username = %s",
                (poll_id, username),
            )
            existing = await row.fetchone()
            if existing:
                return None

        await conn.execute(
            """INSERT INTO poll_votes (id, poll_id, channel, username, option_index, voted_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (vote_id, poll_id, channel, username, option_index, now),
        )
        await conn.commit()
    return {
        "id": vote_id, "poll_id": poll_id, "username": username,
        "option_index": option_index, "voted_at": now,
    }


async def close_poll(channel: str, poll_id: str) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE polls SET status = 'closed', closed_at = %s
               WHERE id = %s AND channel = %s RETURNING *""",
            (now, poll_id, channel),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def get_results(channel: str, poll_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM polls WHERE id = %s AND channel = %s",
            (poll_id, channel),
        )
        poll = await row.fetchone()
        if not poll:
            return None
        poll = dict(poll)

        row = await conn.execute(
            """SELECT option_index, count(*) AS vote_count
               FROM poll_votes WHERE poll_id = %s
               GROUP BY option_index ORDER BY option_index""",
            (poll_id,),
        )
        vote_rows = await row.fetchall()

        row = await conn.execute(
            "SELECT count(*) AS total FROM poll_votes WHERE poll_id = %s",
            (poll_id,),
        )
        total_row = await row.fetchone()
        total_votes = total_row["total"] if total_row else 0

    options = poll["options"] if isinstance(poll["options"], list) else json.loads(poll["options"])
    vote_map = {r["option_index"]: r["vote_count"] for r in vote_rows}

    results = []
    for i, option in enumerate(options):
        count = vote_map.get(i, 0)
        pct = (count / total_votes * 100) if total_votes > 0 else 0.0
        results.append({"option": option, "index": i, "votes": count, "percentage": round(pct, 1)})

    return {
        **poll,
        "total_votes": total_votes,
        "results": results,
    }
