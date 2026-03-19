"""Repository for creative/music streamer features."""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


# ========== Art Commissions ==========
async def list_commissions(channel: str, status: Optional[str] = None) -> list[dict]:
    async with get_conn() as conn:
        if status:
            row = await conn.execute(
                "SELECT * FROM art_commissions WHERE channel = %s AND status = %s ORDER BY created_at DESC",
                (channel, status),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM art_commissions WHERE channel = %s ORDER BY created_at DESC",
                (channel,),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_commission(channel: str, username: str, description: str,
                            reference_url: str, style: str, size: str, price: float) -> dict:
    comm_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO art_commissions (id, channel, username, description, reference_url, style, size, price, status, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)""",
            (comm_id, channel, username, description, reference_url, style, size, price, now),
        )
        await conn.commit()
    return {
        "id": comm_id, "channel": channel, "username": username, "description": description,
        "reference_url": reference_url, "style": style, "size": size, "price": price,
        "status": "pending", "created_at": now,
    }


async def update_commission_status(channel: str, comm_id: str, status: str) -> Optional[dict]:
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE art_commissions SET status = %s WHERE id = %s AND channel = %s",
            (status, comm_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM art_commissions WHERE id = %s", (comm_id,))
        result = await row.fetchone()
    return dict(result) if result else None


async def delete_commission(channel: str, comm_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM art_commissions WHERE id = %s AND channel = %s",
            (comm_id, channel),
        )
        await conn.commit()


# ========== Tutorial Requests ==========
async def list_tutorials(channel: str, status: Optional[str] = None) -> list[dict]:
    async with get_conn() as conn:
        if status:
            row = await conn.execute(
                "SELECT * FROM tutorial_requests WHERE channel = %s AND status = %s ORDER BY votes DESC",
                (channel, status),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM tutorial_requests WHERE channel = %s ORDER BY votes DESC",
                (channel,),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_tutorial(channel: str, username: str, topic: str) -> dict:
    tut_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO tutorial_requests (id, channel, username, topic, votes, status, created_at)
               VALUES (%s, %s, %s, %s, 0, 'pending', %s)""",
            (tut_id, channel, username, topic, now),
        )
        await conn.commit()
    return {
        "id": tut_id, "channel": channel, "username": username,
        "topic": topic, "votes": 0, "status": "pending", "created_at": now,
    }


async def vote_tutorial(channel: str, tut_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE tutorial_requests SET votes = votes + 1 WHERE id = %s AND channel = %s",
            (tut_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM tutorial_requests WHERE id = %s", (tut_id,))
        result = await row.fetchone()
    return dict(result) if result else None


async def complete_tutorial(channel: str, tut_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE tutorial_requests SET status = 'completed' WHERE id = %s AND channel = %s",
            (tut_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM tutorial_requests WHERE id = %s", (tut_id,))
        result = await row.fetchone()
    return dict(result) if result else None


async def delete_tutorial(channel: str, tut_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM tutorial_requests WHERE id = %s AND channel = %s",
            (tut_id, channel),
        )
        await conn.commit()


# ========== Collaboration Requests ==========
async def list_collabs(channel: str, status: Optional[str] = None) -> list[dict]:
    async with get_conn() as conn:
        if status:
            row = await conn.execute(
                "SELECT * FROM collab_requests WHERE channel = %s AND status = %s ORDER BY created_at DESC",
                (channel, status),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM collab_requests WHERE channel = %s ORDER BY created_at DESC",
                (channel,),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_collab(channel: str, requester_username: str,
                        requester_channel: str, proposal: str) -> dict:
    collab_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO collab_requests (id, channel, requester_username, requester_channel, proposal, status, created_at)
               VALUES (%s, %s, %s, %s, %s, 'pending', %s)""",
            (collab_id, channel, requester_username, requester_channel, proposal, now),
        )
        await conn.commit()
    return {
        "id": collab_id, "channel": channel, "requester_username": requester_username,
        "requester_channel": requester_channel, "proposal": proposal,
        "status": "pending", "created_at": now,
    }


async def update_collab_status(channel: str, collab_id: str, status: str) -> Optional[dict]:
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE collab_requests SET status = %s WHERE id = %s AND channel = %s",
            (status, collab_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM collab_requests WHERE id = %s", (collab_id,))
        result = await row.fetchone()
    return dict(result) if result else None


async def delete_collab(channel: str, collab_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM collab_requests WHERE id = %s AND channel = %s",
            (collab_id, channel),
        )
        await conn.commit()
