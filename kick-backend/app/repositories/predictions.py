"""Repository for predictions (viewer point betting)."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def create_prediction(
    channel: str, title: str, outcomes: list[str], lock_seconds: int,
) -> dict:
    pred_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO predictions
               (id, channel, title, outcomes, lock_seconds, status, created_at)
               VALUES (%s, %s, %s, %s, %s, 'open', %s)""",
            (pred_id, channel, title, json.dumps(outcomes), lock_seconds, now),
        )
        await conn.commit()
    return {
        "id": pred_id, "channel": channel, "title": title, "outcomes": outcomes,
        "lock_seconds": lock_seconds, "status": "open", "created_at": now,
    }


async def list_predictions(channel: str, limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM predictions WHERE channel = %s
               ORDER BY created_at DESC LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def get_prediction(channel: str, pred_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM predictions WHERE id = %s AND channel = %s",
            (pred_id, channel),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def place_bet(
    channel: str, pred_id: str, username: str, outcome_index: int, amount: int,
) -> Optional[dict]:
    bet_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        # Check prediction exists and is open
        row = await conn.execute(
            "SELECT * FROM predictions WHERE id = %s AND channel = %s AND status = 'open'",
            (pred_id, channel),
        )
        pred = await row.fetchone()
        if not pred:
            return None

        pred = dict(pred)
        outcomes = pred["outcomes"] if isinstance(pred["outcomes"], list) else json.loads(pred["outcomes"])
        if outcome_index < 0 or outcome_index >= len(outcomes):
            return None

        # Check user has enough points
        row = await conn.execute(
            "SELECT balance FROM loyalty_points WHERE channel = %s AND username = %s",
            (channel, username),
        )
        user_pts = await row.fetchone()
        if not user_pts or user_pts["balance"] < amount:
            return None

        # Deduct points
        new_balance = user_pts["balance"] - amount
        await conn.execute(
            """UPDATE loyalty_points SET balance = %s, total_spent = total_spent + %s, updated_at = %s
               WHERE channel = %s AND username = %s""",
            (new_balance, amount, now, channel, username),
        )

        # Record bet
        await conn.execute(
            """INSERT INTO prediction_bets
               (id, prediction_id, channel, username, outcome_index, amount, status, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s)""",
            (bet_id, pred_id, channel, username, outcome_index, amount, now),
        )
        await conn.commit()
    return {
        "id": bet_id, "prediction_id": pred_id, "username": username,
        "outcome_index": outcome_index, "amount": amount,
        "status": "pending", "created_at": now,
    }


async def lock_prediction(channel: str, pred_id: str) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE predictions SET status = 'locked', locked_at = %s
               WHERE id = %s AND channel = %s AND status = 'open' RETURNING *""",
            (now, pred_id, channel),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def resolve_prediction(
    channel: str, pred_id: str, winning_index: int,
) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        # Get prediction
        row = await conn.execute(
            "SELECT * FROM predictions WHERE id = %s AND channel = %s",
            (pred_id, channel),
        )
        pred = await row.fetchone()
        if not pred or pred["status"] not in ("open", "locked"):
            return None
        pred = dict(pred)

        # Get total bet pool and winning pool
        row = await conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM prediction_bets WHERE prediction_id = %s",
            (pred_id,),
        )
        total_pool = (await row.fetchone())["total"]

        row = await conn.execute(
            """SELECT COALESCE(SUM(amount), 0) AS winning_total
               FROM prediction_bets WHERE prediction_id = %s AND outcome_index = %s""",
            (pred_id, winning_index),
        )
        winning_pool = (await row.fetchone())["winning_total"]

        # Distribute winnings proportionally
        if winning_pool > 0 and total_pool > 0:
            row = await conn.execute(
                """SELECT id, username, amount FROM prediction_bets
                   WHERE prediction_id = %s AND outcome_index = %s""",
                (pred_id, winning_index),
            )
            winners = await row.fetchall()
            for winner in winners:
                payout = int(winner["amount"] * total_pool / winning_pool)
                await conn.execute(
                    """UPDATE loyalty_points
                       SET balance = balance + %s, total_earned = total_earned + %s, updated_at = %s
                       WHERE channel = %s AND username = %s""",
                    (payout, payout, now, channel, winner["username"]),
                )
                await conn.execute(
                    "UPDATE prediction_bets SET status = 'won', payout = %s WHERE id = %s",
                    (payout, winner["id"]),
                )

        # Mark losing bets
        await conn.execute(
            """UPDATE prediction_bets SET status = 'lost', payout = 0
               WHERE prediction_id = %s AND outcome_index != %s AND status = 'pending'""",
            (pred_id, winning_index),
        )

        # Update prediction status
        row = await conn.execute(
            """UPDATE predictions SET status = 'resolved', winning_index = %s, resolved_at = %s
               WHERE id = %s RETURNING *""",
            (winning_index, now, pred_id),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def cancel_prediction(channel: str, pred_id: str) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        # Refund all bets
        row = await conn.execute(
            "SELECT username, amount FROM prediction_bets WHERE prediction_id = %s AND status = 'pending'",
            (pred_id,),
        )
        bets = await row.fetchall()
        for bet in bets:
            await conn.execute(
                """UPDATE loyalty_points
                   SET balance = balance + %s, total_spent = total_spent - %s, updated_at = %s
                   WHERE channel = %s AND username = %s""",
                (bet["amount"], bet["amount"], now, channel, bet["username"]),
            )

        await conn.execute(
            "UPDATE prediction_bets SET status = 'refunded' WHERE prediction_id = %s",
            (pred_id,),
        )

        row = await conn.execute(
            """UPDATE predictions SET status = 'cancelled', resolved_at = %s
               WHERE id = %s AND channel = %s RETURNING *""",
            (now, pred_id, channel),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def get_prediction_details(channel: str, pred_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM predictions WHERE id = %s AND channel = %s",
            (pred_id, channel),
        )
        pred = await row.fetchone()
        if not pred:
            return None
        pred = dict(pred)

        row = await conn.execute(
            """SELECT outcome_index, count(*) AS bet_count, COALESCE(SUM(amount), 0) AS total_amount
               FROM prediction_bets WHERE prediction_id = %s
               GROUP BY outcome_index ORDER BY outcome_index""",
            (pred_id,),
        )
        bet_rows = await row.fetchall()

        row = await conn.execute(
            "SELECT count(*) AS total_bettors, COALESCE(SUM(amount), 0) AS total_pool FROM prediction_bets WHERE prediction_id = %s",
            (pred_id,),
        )
        totals = await row.fetchone()

    outcomes = pred["outcomes"] if isinstance(pred["outcomes"], list) else json.loads(pred["outcomes"])
    bet_map = {r["outcome_index"]: {"bet_count": r["bet_count"], "total_amount": r["total_amount"]} for r in bet_rows}

    outcome_details = []
    for i, outcome in enumerate(outcomes):
        info = bet_map.get(i, {"bet_count": 0, "total_amount": 0})
        outcome_details.append({
            "index": i, "title": outcome,
            "bet_count": info["bet_count"], "total_amount": info["total_amount"],
        })

    return {
        **pred,
        "total_bettors": totals["total_bettors"] if totals else 0,
        "total_pool": totals["total_pool"] if totals else 0,
        "outcome_details": outcome_details,
    }
