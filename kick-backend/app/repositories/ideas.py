"""Repository for giveaway ideas data access."""

import json

from app.services.db import get_conn, _generate_id


async def list_saved() -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM saved_ideas")
        return [dict(i) for i in await row.fetchall()]


async def save_idea(title: str, description: str, category: str, estimated_cost: str, engagement_level: str, requirements: list[str]) -> dict:
    idea_id = _generate_id()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO saved_ideas (id, title, description, category, estimated_cost, engagement_level, requirements, saved)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (idea_id, title, description, category, estimated_cost,
             engagement_level, json.dumps(requirements), True),
        )
        await conn.commit()
    return {
        "id": idea_id, "title": title, "description": description,
        "category": category, "estimated_cost": estimated_cost,
        "engagement_level": engagement_level, "requirements": requirements,
        "saved": True,
    }


async def delete_saved(idea_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM saved_ideas WHERE id = %s", (idea_id,))
        await conn.commit()
