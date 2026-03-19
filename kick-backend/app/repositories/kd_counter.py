"""Repository for kill/death counter."""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def get_counter(channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM kd_counters WHERE channel = %s ORDER BY updated_at DESC LIMIT 1",
            (channel,),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def create_counter(channel: str, game: str = "") -> dict:
    counter_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO kd_counters (id, channel, game, kills, deaths, assists, updated_at)
               VALUES (%s, %s, %s, 0, 0, 0, %s)""",
            (counter_id, channel, game, now),
        )
        await conn.commit()
    return {
        "id": counter_id, "channel": channel, "game": game,
        "kills": 0, "deaths": 0, "assists": 0, "updated_at": now,
    }


async def update_counter(channel: str, counter_id: str, **kwargs) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM kd_counters WHERE id = %s AND channel = %s",
            (counter_id, channel),
        )
        existing = await row.fetchone()
        if not existing:
            return None

        data = dict(existing)
        data.update(kwargs)
        data["updated_at"] = now
        await conn.execute(
            """UPDATE kd_counters SET kills = %s, deaths = %s, assists = %s, game = %s, updated_at = %s
               WHERE id = %s AND channel = %s""",
            (data["kills"], data["deaths"], data["assists"], data["game"], now, counter_id, channel),
        )
        await conn.commit()
    return data


async def increment(channel: str, counter_id: str, field: str, amount: int = 1) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM kd_counters WHERE id = %s AND channel = %s",
            (counter_id, channel),
        )
        existing = await row.fetchone()
        if not existing:
            return None

        now = _now_iso()
        new_val = existing[field] + amount
        await conn.execute(
            f"UPDATE kd_counters SET {field} = %s, updated_at = %s WHERE id = %s AND channel = %s",
            (new_val, now, counter_id, channel),
        )
        await conn.commit()

    data = dict(existing)
    data[field] = new_val
    data["updated_at"] = now
    return data


async def reset_counter(channel: str, counter_id: str) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE kd_counters SET kills = 0, deaths = 0, assists = 0, updated_at = %s WHERE id = %s AND channel = %s",
            (now, counter_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM kd_counters WHERE id = %s", (counter_id,))
        result = await row.fetchone()
    return dict(result) if result else None
