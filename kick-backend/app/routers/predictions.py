"""Predictions System router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import PredictionCreate, PredictionBet, PredictionResolve
from app.repositories import predictions as pred_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("/{channel}")
async def list_predictions(
    channel: str,
    status: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await pred_repo.list_predictions(channel, status)


@router.post("/{channel}")
async def create_prediction(
    channel: str, body: PredictionCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await pred_repo.create_prediction(
        channel=channel, title=body.title, outcomes=body.outcomes,
        lock_seconds=body.lock_seconds,
    )
    logger.info("Prediction '%s' created for channel=%s", body.title, channel)
    return result


@router.post("/{channel}/{pred_id}/bet")
async def place_bet(
    channel: str, pred_id: str, body: PredictionBet, _session: dict = Depends(require_auth)
) -> dict:
    result = await pred_repo.place_bet(channel, pred_id, body.username, body.outcome_index, body.amount)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot place bet. Prediction may be locked or you already bet.")
    return result


@router.post("/{channel}/{pred_id}/lock")
async def lock_prediction(
    channel: str, pred_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await pred_repo.lock_prediction(channel, pred_id)
    if not result:
        raise HTTPException(status_code=404, detail="Prediction not found")
    logger.info("Prediction %s locked for channel=%s", pred_id, channel)
    return result


@router.post("/{channel}/{pred_id}/resolve")
async def resolve_prediction(
    channel: str, pred_id: str, body: PredictionResolve,
    _session: dict = Depends(require_auth),
) -> dict:
    result = await pred_repo.resolve_prediction(channel, pred_id, body.winning_outcome_index)
    if not result:
        raise HTTPException(status_code=404, detail="Prediction not found")
    logger.info("Prediction %s resolved for channel=%s (winner=%d)", pred_id, channel, body.winning_outcome_index)
    return result


@router.post("/{channel}/{pred_id}/cancel")
async def cancel_prediction(
    channel: str, pred_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await pred_repo.cancel_prediction(channel, pred_id)
    if not result:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return result
