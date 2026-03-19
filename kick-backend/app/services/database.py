"""Database helper — re-exports used by routers that haven't been migrated yet."""

from app.services.db import _generate_id as generate_id, _now_iso as now_iso

__all__ = ["generate_id", "now_iso"]
