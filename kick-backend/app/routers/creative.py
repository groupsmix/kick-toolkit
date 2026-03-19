"""Creative/Music Streamer Features router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import (
    ArtCommissionCreate, TutorialRequestCreate, CollabRequestCreate,
)
from app.repositories import creative as creative_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/creative", tags=["creative"])


# ========== Art Commissions ==========
@router.get("/commissions/{channel}")
async def list_commissions(
    channel: str,
    status: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await creative_repo.list_commissions(channel, status)


@router.post("/commissions/{channel}")
async def create_commission(
    channel: str, body: ArtCommissionCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await creative_repo.create_commission(
        channel, body.username, body.description, body.reference_url,
        body.style, body.size, body.price,
    )
    logger.info("Art commission created for channel=%s by %s", channel, body.username)
    return result


@router.post("/commissions/{channel}/{comm_id}/status")
async def update_commission_status(
    channel: str, comm_id: str, status: str = Query(...),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await creative_repo.update_commission_status(channel, comm_id, status)
    if not result:
        raise HTTPException(status_code=404, detail="Commission not found")
    return result


@router.delete("/commissions/{channel}/{comm_id}")
async def delete_commission(
    channel: str, comm_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await creative_repo.delete_commission(channel, comm_id)
    return {"status": "deleted"}


# ========== Tutorial Requests ==========
@router.get("/tutorials/{channel}")
async def list_tutorials(
    channel: str,
    status: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await creative_repo.list_tutorials(channel, status)


@router.post("/tutorials/{channel}")
async def create_tutorial(
    channel: str, body: TutorialRequestCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await creative_repo.create_tutorial(channel, body.username, body.topic)
    return result


@router.post("/tutorials/{channel}/{tut_id}/vote")
async def vote_tutorial(
    channel: str, tut_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await creative_repo.vote_tutorial(channel, tut_id)
    if not result:
        raise HTTPException(status_code=404, detail="Tutorial request not found")
    return result


@router.post("/tutorials/{channel}/{tut_id}/complete")
async def complete_tutorial(
    channel: str, tut_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await creative_repo.complete_tutorial(channel, tut_id)
    if not result:
        raise HTTPException(status_code=404, detail="Tutorial request not found")
    return result


@router.delete("/tutorials/{channel}/{tut_id}")
async def delete_tutorial(
    channel: str, tut_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await creative_repo.delete_tutorial(channel, tut_id)
    return {"status": "deleted"}


# ========== Collaboration Requests ==========
@router.get("/collabs/{channel}")
async def list_collabs(
    channel: str,
    status: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await creative_repo.list_collabs(channel, status)


@router.post("/collabs/{channel}")
async def create_collab(
    channel: str, body: CollabRequestCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await creative_repo.create_collab(
        channel, body.requester_username, body.requester_channel, body.proposal,
    )
    logger.info("Collab request from %s for channel=%s", body.requester_username, channel)
    return result


@router.post("/collabs/{channel}/{collab_id}/status")
async def update_collab_status(
    channel: str, collab_id: str, status: str = Query(...),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await creative_repo.update_collab_status(channel, collab_id, status)
    if not result:
        raise HTTPException(status_code=404, detail="Collaboration request not found")
    return result


@router.delete("/collabs/{channel}/{collab_id}")
async def delete_collab(
    channel: str, collab_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await creative_repo.delete_collab(channel, collab_id)
    return {"status": "deleted"}
