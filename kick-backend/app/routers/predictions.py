"""Predictions System (Viewer Point Betting) router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import PredictionCreate, PredictionBet, PredictionResolve
from app.repositories import predictions as predictions_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.post("/{channel}")
async def create_prediction(
    channel: str, body: PredictionCreate, _session: dict = Depends(require_auth)
) -> dict:
    if len(body.outcomes) < 2:
        raise HTTPException(status_code=400, detail="Prediction must have at least 2 outcomes")
    if len(body.outcomes) > 10:
        raise HTTPException(status_code=400, detail="Prediction can have at most 10 outcomes")
    result = await predictions_repo.create_prediction(
        channel, body.title, body.outcomes, body.lock_seconds,
    )
    logger.info("Prediction '%s' created for channel=%s", body.title, channel)
    return result


@router.get("/{channel}")
async def list_predictions(
    channel: str,
    limit: int = Query(default=20, le=100),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await predictions_repo.list_predictions(channel, limit)


@router.get("/{channel}/{pred_id}")
async def get_prediction(
    channel: str, pred_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await predictions_repo.get_prediction_details(channel, pred_id)
    if not result:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return result


@router.post("/{channel}/{pred_id}/bet")
async def place_bet(
    channel: str, pred_id: str, body: PredictionBet,
    _session: dict = Depends(require_auth),
) -> dict:
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Bet amount must be positive")
    result = await predictions_repo.place_bet(
        channel, pred_id, body.username, body.outcome_index, body.amount,
    )
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Cannot place bet. Prediction may be closed, outcome invalid, or insufficient points.",
        )
    logger.info(
        "Bet placed by %s on prediction %s: %d points on outcome %d",
        body.username, pred_id, body.amount, body.outcome_index,
    )
    return result


@router.post("/{channel}/{pred_id}/lock")
async def lock_prediction(
    channel: str, pred_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await predictions_repo.lock_prediction(channel, pred_id)
    if not result:
        raise HTTPException(status_code=404, detail="Prediction not found or already locked")
    logger.info("Prediction %s locked in channel=%s", pred_id, channel)
    return result


@router.post("/{channel}/{pred_id}/resolve")
async def resolve_prediction(
    channel: str, pred_id: str, body: PredictionResolve,
    _session: dict = Depends(require_auth),
) -> dict:
    result = await predictions_repo.resolve_prediction(channel, pred_id, body.winning_index)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot resolve. Prediction may already be resolved.")
    logger.info("Prediction %s resolved in channel=%s, winning index=%d", pred_id, channel, body.winning_index)
    return result


@router.post("/{channel}/{pred_id}/cancel")
async def cancel_prediction(
    channel: str, pred_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await predictions_repo.cancel_prediction(channel, pred_id)
    if not result:
        raise HTTPException(status_code=404, detail="Prediction not found")
    logger.info("Prediction %s cancelled in channel=%s", pred_id, channel)
    return result
