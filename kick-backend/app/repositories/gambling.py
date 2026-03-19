"""Repository for gambling streamer features."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


# ========== Slot Request Queue ==========
async def list_slot_requests(channel: str, status: Optional[str] = None) -> list[dict]:
    async with get_conn() as conn:
        if status:
            row = await conn.execute(
                "SELECT * FROM slot_requests WHERE channel = %s AND status = %s ORDER BY position ASC",
                (channel, status),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM slot_requests WHERE channel = %s ORDER BY position ASC",
                (channel,),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_slot_request(channel: str, username: str, slot_name: str, note: str = "") -> Optional[dict]:
    # Check if slot is banned
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM banned_slots WHERE channel = %s AND LOWER(slot_name) = LOWER(%s)",
            (channel, slot_name),
        )
        banned = await row.fetchone()
        if banned:
            return None

        # Get next position
        row = await conn.execute(
            "SELECT COALESCE(MAX(position), 0) + 1 as next_pos FROM slot_requests WHERE channel = %s AND status = 'pending'",
            (channel,),
        )
        pos_result = await row.fetchone()
        next_pos = pos_result["next_pos"] if pos_result else 1

        req_id = _generate_id()
        now = _now_iso()
        await conn.execute(
            """INSERT INTO slot_requests (id, channel, username, slot_name, note, status, position, created_at)
               VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s)""",
            (req_id, channel, username, slot_name, note, next_pos, now),
        )
        await conn.commit()
    return {
        "id": req_id, "channel": channel, "username": username, "slot_name": slot_name,
        "note": note, "status": "pending", "position": next_pos, "created_at": now,
    }


async def update_slot_request_status(channel: str, req_id: str, status: str) -> Optional[dict]:
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE slot_requests SET status = %s WHERE id = %s AND channel = %s",
            (status, req_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM slot_requests WHERE id = %s", (req_id,))
        result = await row.fetchone()
    return dict(result) if result else None


async def delete_slot_request(channel: str, req_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM slot_requests WHERE id = %s AND channel = %s",
            (req_id, channel),
        )
        await conn.commit()


# ========== Banned Slots ==========
async def list_banned_slots(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM banned_slots WHERE channel = %s ORDER BY added_at DESC",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def add_banned_slot(channel: str, slot_name: str, reason: str = "") -> dict:
    slot_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO banned_slots (id, channel, slot_name, reason, added_at)
               VALUES (%s, %s, %s, %s, %s) ON CONFLICT (channel, slot_name) DO NOTHING""",
            (slot_id, channel, slot_name, reason, now),
        )
        await conn.commit()
    return {"id": slot_id, "channel": channel, "slot_name": slot_name, "reason": reason, "added_at": now}


async def remove_banned_slot(channel: str, slot_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM banned_slots WHERE id = %s AND channel = %s",
            (slot_id, channel),
        )
        await conn.commit()


# ========== Gambling Sessions ==========
async def get_active_session(channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM gambling_sessions WHERE channel = %s AND status = 'active' ORDER BY started_at DESC LIMIT 1",
            (channel,),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def list_sessions(channel: str, limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM gambling_sessions WHERE channel = %s ORDER BY started_at DESC LIMIT %s",
            (channel, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_session(channel: str, start_balance: float) -> dict:
    session_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO gambling_sessions (id, channel, start_balance, current_balance, total_wagered,
               total_won, biggest_win, biggest_loss, status, started_at)
               VALUES (%s, %s, %s, %s, 0.0, 0.0, 0.0, 0.0, 'active', %s)""",
            (session_id, channel, start_balance, start_balance, now),
        )
        await conn.commit()
    return {
        "id": session_id, "channel": channel, "start_balance": start_balance,
        "current_balance": start_balance, "total_wagered": 0.0, "total_won": 0.0,
        "biggest_win": 0.0, "biggest_loss": 0.0, "status": "active", "started_at": now,
    }


async def update_session(channel: str, session_id: str, **kwargs) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM gambling_sessions WHERE id = %s AND channel = %s",
            (session_id, channel),
        )
        existing = await row.fetchone()
        if not existing:
            return None

        data = dict(existing)
        data.update(kwargs)
        if kwargs.get("status") == "ended":
            data["ended_at"] = _now_iso()

        await conn.execute(
            """UPDATE gambling_sessions SET current_balance = %s, total_wagered = %s, total_won = %s,
               biggest_win = %s, biggest_loss = %s, status = %s, ended_at = %s
               WHERE id = %s AND channel = %s""",
            (data["current_balance"], data["total_wagered"], data["total_won"],
             data["biggest_win"], data["biggest_loss"], data["status"],
             data.get("ended_at"), session_id, channel),
        )
        await conn.commit()
    return data


async def end_session(channel: str, session_id: str) -> Optional[dict]:
    return await update_session(channel, session_id, status="ended")


# ========== Bet Log ==========
async def list_bets(channel: str, session_id: str, limit: int = 100) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM bet_logs WHERE channel = %s AND session_id = %s ORDER BY created_at DESC LIMIT %s",
            (channel, session_id, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def log_bet(channel: str, session_id: str, slot_name: str,
                  bet_amount: float, win_amount: float, result: str) -> dict:
    bet_id = _generate_id()
    now = _now_iso()

    # Update session stats
    session = await get_active_session(channel)
    running_total = 0.0
    if session:
        net = win_amount - bet_amount
        new_balance = session["current_balance"] + net
        new_wagered = session["total_wagered"] + bet_amount
        new_won = session["total_won"] + win_amount
        biggest_win = max(session["biggest_win"], win_amount - bet_amount if result == "win" else 0)
        biggest_loss = max(session["biggest_loss"], bet_amount - win_amount if result == "loss" else 0)
        running_total = new_balance - session["start_balance"]
        await update_session(
            channel, session_id,
            current_balance=new_balance, total_wagered=new_wagered,
            total_won=new_won, biggest_win=biggest_win, biggest_loss=biggest_loss,
        )

    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO bet_logs (id, channel, session_id, slot_name, bet_amount, win_amount, result, running_total, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (bet_id, channel, session_id, slot_name, bet_amount, win_amount, result, running_total, now),
        )
        await conn.commit()
    return {
        "id": bet_id, "channel": channel, "session_id": session_id,
        "slot_name": slot_name, "bet_amount": bet_amount, "win_amount": win_amount,
        "result": result, "running_total": running_total, "created_at": now,
    }


# ========== Slot Ratings ==========
async def list_slot_ratings(channel: str, slot_name: Optional[str] = None) -> list[dict]:
    async with get_conn() as conn:
        if slot_name:
            row = await conn.execute(
                "SELECT * FROM slot_ratings WHERE channel = %s AND slot_name = %s ORDER BY created_at DESC",
                (channel, slot_name),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM slot_ratings WHERE channel = %s ORDER BY created_at DESC",
                (channel,),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def rate_slot(channel: str, username: str, slot_name: str, rating: int, comment: str = "") -> dict:
    rating_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO slot_ratings (id, channel, username, slot_name, rating, comment, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (channel, username, slot_name) DO UPDATE SET
                   rating = EXCLUDED.rating, comment = EXCLUDED.comment, created_at = EXCLUDED.created_at""",
            (rating_id, channel, username, slot_name, rating, comment, now),
        )
        await conn.commit()
    return {
        "id": rating_id, "channel": channel, "username": username,
        "slot_name": slot_name, "rating": rating, "comment": comment, "created_at": now,
    }


async def get_slot_stats(channel: str) -> list[dict]:
    """Get hot/cold slot stats."""
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT slot_name,
                      COUNT(*) as total_bets,
                      SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                      SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
                      SUM(win_amount - bet_amount) as net_profit,
                      AVG(CASE WHEN result = 'win' THEN win_amount ELSE 0 END) as avg_win
               FROM bet_logs WHERE channel = %s AND slot_name != '' GROUP BY slot_name
               ORDER BY net_profit DESC""",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


# ========== Balance Milestones ==========
async def list_milestones(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM balance_milestones WHERE channel = %s ORDER BY triggered_at DESC",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def add_milestone(channel: str, amount: float, direction: str = "up") -> dict:
    ms_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            "INSERT INTO balance_milestones (id, channel, amount, direction, triggered_at) VALUES (%s, %s, %s, %s, %s)",
            (ms_id, channel, amount, direction, now),
        )
        await conn.commit()
    return {"id": ms_id, "channel": channel, "amount": amount, "direction": direction, "triggered_at": now}


# ========== Rain/Tip Tracker ==========
async def list_rain_events(channel: str, limit: int = 50) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM rain_events WHERE channel = %s ORDER BY created_at DESC LIMIT %s",
            (channel, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_rain_event(channel: str, amount: float, currency: str, source: str, tip_count: int) -> dict:
    event_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO rain_events (id, channel, amount, currency, source, tip_count, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (event_id, channel, amount, currency, source, tip_count, now),
        )
        await conn.commit()
    return {
        "id": event_id, "channel": channel, "amount": amount, "currency": currency,
        "source": source, "tip_count": tip_count, "created_at": now,
    }


async def get_rain_stats(channel: str) -> dict:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT COALESCE(SUM(amount), 0) as total_rain,
                      COUNT(*) as total_events,
                      COALESCE(SUM(tip_count), 0) as total_tips,
                      COALESCE(MAX(amount), 0) as biggest_rain
               FROM rain_events WHERE channel = %s""",
            (channel,),
        )
        result = await row.fetchone()
    return dict(result) if result else {"total_rain": 0, "total_events": 0, "total_tips": 0, "biggest_rain": 0}
