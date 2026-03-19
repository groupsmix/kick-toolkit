"""Base repository class that consolidates common CRUD boilerplate.

All 34 repository modules follow the same pattern:
  - ``async with get_conn() as conn`` for every operation
  - ``_generate_id()`` / ``_now_iso()`` for new rows
  - ``dict(row)`` conversion on results

This base class extracts those patterns so domain repositories can inherit
and reduce boilerplate while still writing custom SQL when needed.
"""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


class BaseRepository:
    """Lightweight base class for raw-SQL repository modules."""

    def __init__(self, table: str) -> None:
        self.table = table

    # ---- helpers available to subclasses ----

    @staticmethod
    def generate_id() -> str:
        return _generate_id()

    @staticmethod
    def now_iso() -> str:
        return _now_iso()

    # ---- generic CRUD ----

    async def get_by_id(self, row_id: str) -> Optional[dict]:
        """Fetch a single row by its primary key ``id``."""
        async with get_conn() as conn:
            cur = await conn.execute(
                f"SELECT * FROM {self.table} WHERE id = %s", (row_id,)
            )
            row = await cur.fetchone()
        return dict(row) if row else None

    async def get_by_channel(self, channel: str) -> Optional[dict]:
        """Fetch a single row scoped to *channel*."""
        async with get_conn() as conn:
            cur = await conn.execute(
                f"SELECT * FROM {self.table} WHERE channel = %s", (channel,)
            )
            row = await cur.fetchone()
        return dict(row) if row else None

    async def list_by_channel(
        self,
        channel: str,
        order_by: str = "created_at DESC",
    ) -> list[dict]:
        """Return all rows for a channel, ordered by *order_by*."""
        async with get_conn() as conn:
            cur = await conn.execute(
                f"SELECT * FROM {self.table} WHERE channel = %s ORDER BY {order_by}",
                (channel,),
            )
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def delete_by_id(self, row_id: str) -> None:
        """Delete a row by its primary key ``id``."""
        async with get_conn() as conn:
            await conn.execute(
                f"DELETE FROM {self.table} WHERE id = %s", (row_id,)
            )
            await conn.commit()

    async def delete_by_id_and_channel(
        self, row_id: str, channel: str
    ) -> None:
        """Delete a row scoped to both ``id`` and ``channel``."""
        async with get_conn() as conn:
            await conn.execute(
                f"DELETE FROM {self.table} WHERE id = %s AND channel = %s",
                (row_id, channel),
            )
            await conn.commit()

    async def count_by_channel(self, channel: str) -> int:
        """Return the number of rows for a channel."""
        async with get_conn() as conn:
            cur = await conn.execute(
                f"SELECT count(*) AS cnt FROM {self.table} WHERE channel = %s",
                (channel,),
            )
            row = await cur.fetchone()
        return row["cnt"] if row else 0

    async def exists(self, row_id: str) -> bool:
        """Check whether a row with the given id exists."""
        async with get_conn() as conn:
            cur = await conn.execute(
                f"SELECT 1 FROM {self.table} WHERE id = %s", (row_id,)
            )
            row = await cur.fetchone()
        return row is not None
