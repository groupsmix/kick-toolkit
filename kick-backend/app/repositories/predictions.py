"""Repository for predictions system."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def list_predictions(channel: str, status: Optional[str] = None) -> list[dict]:
    async with get_conn() as conn:
        if status:
            row = await conn.execute(
                "SELECT * FROM predictions WHERE channel = %s AND status = %s ORDER BY created_at DESC",
                (channel, status),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM predictions WHERE channel = %s ORDER BY created_at DESC",
                (channel,),
            )
        results = await row.fetchall()
    out = []
    for r in results:
        d = dict(r)
        for key in ("outcomes", "bets"):
            if isinstance(d.get(key), str):
                d[key] = json.loads(d[key])
        if isinstance(d.get("outcome_pools"), str):
            d["outcome_pools"] = json.loads(d["outcome_pools"])
        out.append(d)
    return out


async def create_prediction(channel: str, title: str, outcomes: list[str], lock_seconds: int) -> dict:
    pred_id = _generate_id()
    now = _now_iso()
    pools = {str(i): 0 for i in range(len(outcomes))}
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO predictions (id, channel, title, outcomes, outcome_pools, bets, status, lock_seconds, created_at)
               VALUES (%s, %s, %s, %s, %s, '[]', 'open', %s, %s)""",
            (pred_id, channel, title, json.dumps(outcomes), json.dumps(pools), lock_seconds, now),
        )
        await conn.commit()
    return {
        "id": pred_id, "channel": channel, "title": title, "outcomes": outcomes,
        "outcome_pools": pools, "bets": [], "status": "open",
        "lock_seconds": lock_seconds, "created_at": now,
    }


async def place_bet(channel: str, pred_id: str, username: str, outcome_index: int, amount: int) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM predictions WHERE id = %s AND channel = %s AND status = 'open'",
            (pred_id, channel),
        )
        pred = await row.fetchone()
        if not pred:
            return None

        bets = json.loads(pred["bets"]) if isinstance(pred["bets"], str) else pred["bets"]
        pools = json.loads(pred["outcome_pools"]) if isinstance(pred["outcome_pools"], str) else pred["outcome_pools"]

        # Check if user already bet
        for b in bets:
            if b["username"] == username:
                return None

        bets.append({"username": username, "outcome_index": outcome_index, "amount": amount})
        key = str(outcome_index)
        pools[key] = pools.get(key, 0) + amount

        await conn.execute(
            "UPDATE predictions SET bets = %s, outcome_pools = %s WHERE id = %s AND channel = %s",
            (json.dumps(bets), json.dumps(pools), pred_id, channel),
        )
        await conn.commit()

    outcomes = json.loads(pred["outcomes"]) if isinstance(pred["outcomes"], str) else pred["outcomes"]
    return {
        "id": pred_id, "channel": channel, "title": pred["title"], "outcomes": outcomes,
        "outcome_pools": pools, "bets": bets, "status": "open",
        "lock_seconds": pred["lock_seconds"], "created_at": pred["created_at"],
    }


async def lock_prediction(channel: str, pred_id: str) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE predictions SET status = 'locked', locked_at = %s WHERE id = %s AND channel = %s AND status = 'open'",
            (now, pred_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM predictions WHERE id = %s", (pred_id,))
        result = await row.fetchone()
    if not result:
        return None
    d = dict(result)
    for key in ("outcomes", "bets"):
        if isinstance(d.get(key), str):
            d[key] = json.loads(d[key])
    if isinstance(d.get("outcome_pools"), str):
        d["outcome_pools"] = json.loads(d["outcome_pools"])
    return d


async def resolve_prediction(channel: str, pred_id: str, winning_outcome_index: int) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """UPDATE predictions SET status = 'resolved', winning_outcome_index = %s, resolved_at = %s
               WHERE id = %s AND channel = %s""",
            (winning_outcome_index, now, pred_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM predictions WHERE id = %s", (pred_id,))
        result = await row.fetchone()
    if not result:
        return None
    d = dict(result)
    for key in ("outcomes", "bets"):
        if isinstance(d.get(key), str):
            d[key] = json.loads(d[key])
    if isinstance(d.get("outcome_pools"), str):
        d["outcome_pools"] = json.loads(d["outcome_pools"])
    return d


async def cancel_prediction(channel: str, pred_id: str) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE predictions SET status = 'cancelled', resolved_at = %s WHERE id = %s AND channel = %s",
            (now, pred_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM predictions WHERE id = %s", (pred_id,))
        result = await row.fetchone()
    if not result:
        return None
    d = dict(result)
    for key in ("outcomes", "bets"):
        if isinstance(d.get(key), str):
            d[key] = json.loads(d[key])
    if isinstance(d.get("outcome_pools"), str):
        d["outcome_pools"] = json.loads(d["outcome_pools"])
    return d
