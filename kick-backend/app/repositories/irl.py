"""Repository for IRL streamer features."""

import json
import random
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


# ========== Location ==========
async def get_location(channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM streamer_locations WHERE channel = %s", (channel,)
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def update_location(channel: str, city: str, country: str,
                          latitude: Optional[float] = None,
                          longitude: Optional[float] = None) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO streamer_locations (channel, city, country, latitude, longitude, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (channel) DO UPDATE SET
                   city = EXCLUDED.city, country = EXCLUDED.country,
                   latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude,
                   updated_at = EXCLUDED.updated_at""",
            (channel, city, country, latitude, longitude, now),
        )
        await conn.commit()
    return {
        "channel": channel, "city": city, "country": country,
        "latitude": latitude, "longitude": longitude, "updated_at": now,
    }


# ========== Donation Goals ==========
async def list_goals(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM donation_goals WHERE channel = %s ORDER BY created_at DESC",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_goal(channel: str, title: str, target_amount: float, currency: str) -> dict:
    goal_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO donation_goals (id, channel, title, target_amount, current_amount, currency, status, created_at)
               VALUES (%s, %s, %s, %s, 0.0, %s, 'active', %s)""",
            (goal_id, channel, title, target_amount, currency, now),
        )
        await conn.commit()
    return {
        "id": goal_id, "channel": channel, "title": title,
        "target_amount": target_amount, "current_amount": 0.0,
        "currency": currency, "status": "active", "created_at": now,
    }


async def update_goal(channel: str, goal_id: str, **kwargs) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM donation_goals WHERE id = %s AND channel = %s",
            (goal_id, channel),
        )
        existing = await row.fetchone()
        if not existing:
            return None

        data = dict(existing)
        data.update(kwargs)
        await conn.execute(
            """UPDATE donation_goals SET title = %s, current_amount = %s, status = %s
               WHERE id = %s AND channel = %s""",
            (data["title"], data["current_amount"], data["status"], goal_id, channel),
        )
        await conn.commit()
    return data


async def delete_goal(channel: str, goal_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM donation_goals WHERE id = %s AND channel = %s",
            (goal_id, channel),
        )
        await conn.commit()


# ========== Question Queue ==========
async def list_questions(channel: str, status: Optional[str] = None) -> list[dict]:
    async with get_conn() as conn:
        if status:
            row = await conn.execute(
                "SELECT * FROM questions WHERE channel = %s AND status = %s ORDER BY priority DESC, created_at ASC",
                (channel, status),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM questions WHERE channel = %s ORDER BY priority DESC, created_at ASC",
                (channel,),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_question(channel: str, username: str, question: str, priority: int = 0) -> dict:
    q_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO questions (id, channel, username, question, status, priority, created_at)
               VALUES (%s, %s, %s, %s, 'pending', %s, %s)""",
            (q_id, channel, username, question, priority, now),
        )
        await conn.commit()
    return {
        "id": q_id, "channel": channel, "username": username,
        "question": question, "status": "pending", "priority": priority, "created_at": now,
    }


async def update_question_status(channel: str, q_id: str, status: str) -> Optional[dict]:
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE questions SET status = %s WHERE id = %s AND channel = %s",
            (status, q_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM questions WHERE id = %s", (q_id,))
        result = await row.fetchone()
    return dict(result) if result else None


async def delete_question(channel: str, q_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM questions WHERE id = %s AND channel = %s",
            (q_id, channel),
        )
        await conn.commit()


# ========== Photo Requests ==========
async def list_photo_requests(channel: str, status: Optional[str] = None) -> list[dict]:
    async with get_conn() as conn:
        if status:
            row = await conn.execute(
                "SELECT * FROM photo_requests WHERE channel = %s AND status = %s ORDER BY created_at DESC",
                (channel, status),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM photo_requests WHERE channel = %s ORDER BY created_at DESC",
                (channel,),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_photo_request(channel: str, username: str, description: str, tip_amount: float = 0.0) -> dict:
    req_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO photo_requests (id, channel, username, description, status, tip_amount, created_at)
               VALUES (%s, %s, %s, %s, 'pending', %s, %s)""",
            (req_id, channel, username, description, tip_amount, now),
        )
        await conn.commit()
    return {
        "id": req_id, "channel": channel, "username": username,
        "description": description, "status": "pending",
        "tip_amount": tip_amount, "created_at": now,
    }


async def update_photo_request_status(channel: str, req_id: str, status: str) -> Optional[dict]:
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE photo_requests SET status = %s WHERE id = %s AND channel = %s",
            (status, req_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM photo_requests WHERE id = %s", (req_id,))
        result = await row.fetchone()
    return dict(result) if result else None


# ========== Challenge Wheel ==========
async def list_wheel_challenges(channel: str, unused_only: bool = False) -> list[dict]:
    async with get_conn() as conn:
        if unused_only:
            row = await conn.execute(
                "SELECT * FROM wheel_challenges WHERE channel = %s AND used = FALSE ORDER BY created_at ASC",
                (channel,),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM wheel_challenges WHERE channel = %s ORDER BY created_at ASC",
                (channel,),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def add_wheel_challenge(channel: str, challenge_text: str, username: str = "") -> dict:
    ch_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO wheel_challenges (id, channel, username, challenge_text, used, created_at)
               VALUES (%s, %s, %s, %s, FALSE, %s)""",
            (ch_id, channel, username, challenge_text, now),
        )
        await conn.commit()
    return {
        "id": ch_id, "channel": channel, "username": username,
        "challenge_text": challenge_text, "used": False, "created_at": now,
    }


async def spin_wheel(channel: str) -> Optional[dict]:
    challenges = await list_wheel_challenges(channel, unused_only=True)
    if not challenges:
        return None
    chosen = random.choice(challenges)
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE wheel_challenges SET used = TRUE WHERE id = %s AND channel = %s",
            (chosen["id"], channel),
        )
        await conn.commit()
    chosen["used"] = True
    return chosen


async def delete_wheel_challenge(channel: str, ch_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM wheel_challenges WHERE id = %s AND channel = %s",
            (ch_id, channel),
        )
        await conn.commit()


# ========== Countdown Timer ==========
async def list_timers(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM countdown_timers WHERE channel = %s ORDER BY created_at DESC",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_timer(channel: str, title: str, end_time: str, style: str = "default") -> dict:
    timer_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO countdown_timers (id, channel, title, end_time, style, active, created_at)
               VALUES (%s, %s, %s, %s, %s, TRUE, %s)""",
            (timer_id, channel, title, end_time, style, now),
        )
        await conn.commit()
    return {
        "id": timer_id, "channel": channel, "title": title,
        "end_time": end_time, "style": style, "active": True, "created_at": now,
    }


async def update_timer(channel: str, timer_id: str, active: bool) -> Optional[dict]:
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE countdown_timers SET active = %s WHERE id = %s AND channel = %s",
            (active, timer_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM countdown_timers WHERE id = %s", (timer_id,))
        result = await row.fetchone()
    return dict(result) if result else None


async def delete_timer(channel: str, timer_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM countdown_timers WHERE id = %s AND channel = %s",
            (timer_id, channel),
        )
        await conn.commit()
