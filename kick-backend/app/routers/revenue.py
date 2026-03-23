"""Revenue Intelligence router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import RevenueEntryCreate
from app.repositories import revenue as revenue_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/revenue", tags=["revenue"])


@router.get("/summary/{channel}")
async def get_summary(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    return await revenue_repo.get_summary(channel)


@router.get("/entries/{channel}")
async def get_entries(
    channel: str,
    limit: int = Query(default=100, le=500),
    session: dict = Depends(require_auth),
) -> list[dict]:
    require_channel_owner(session, channel)
    return await revenue_repo.get_entries(channel, limit)


@router.post("/entries/{channel}")
async def create_entry(
    channel: str,
    body: RevenueEntryCreate,
    session: dict = Depends(require_auth),
) -> dict:
    require_channel_owner(session, channel)
    result = await revenue_repo.create_entry(
        channel=channel,
        source=body.source,
        amount=body.amount,
        currency=body.currency,
        description=body.description,
        stream_session_id=body.stream_session_id,
        date=body.date,
    )
    logger.info("Revenue entry created for channel=%s amount=%.2f", channel, body.amount)
    return result


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str, session: dict = Depends(require_auth)) -> dict:
    entry = await revenue_repo.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    require_channel_owner(session, entry["channel"])
    await revenue_repo.delete_entry(entry_id)
    return {"deleted": True}


@router.get("/export/{channel}")
async def export_csv(channel: str, session: dict = Depends(require_auth)) -> PlainTextResponse:
    require_channel_owner(session, channel)
    csv_data = await revenue_repo.export_csv(channel)
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=revenue_{channel}.csv"},
    )
