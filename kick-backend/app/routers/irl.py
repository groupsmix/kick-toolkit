"""IRL Streamer Features router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import (
    StreamerLocationUpdate, DonationGoalCreate, DonationGoalUpdate,
    QuestionCreate, PhotoRequestCreate, WheelChallengeCreate,
    CountdownTimerCreate,
)
from app.repositories import irl as irl_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/irl", tags=["irl"])


# ========== Location ==========
@router.get("/location/{channel}")
async def get_location(channel: str, _session: dict = Depends(require_auth)) -> dict:
    loc = await irl_repo.get_location(channel)
    if not loc:
        return {"channel": channel, "city": "", "country": ""}
    return loc


@router.post("/location/{channel}")
async def update_location(
    channel: str, body: StreamerLocationUpdate, _session: dict = Depends(require_auth)
) -> dict:
    result = await irl_repo.update_location(
        channel, body.city, body.country, body.latitude, body.longitude,
    )
    logger.info("Location updated for channel=%s: %s, %s", channel, body.city, body.country)
    return result


# ========== Donation Goals ==========
@router.get("/goals/{channel}")
async def list_goals(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await irl_repo.list_goals(channel)


@router.post("/goals/{channel}")
async def create_goal(
    channel: str, body: DonationGoalCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await irl_repo.create_goal(channel, body.title, body.target_amount, body.currency)
    logger.info("Donation goal '%s' created for channel=%s", body.title, channel)
    return result


@router.put("/goals/{channel}/{goal_id}")
async def update_goal(
    channel: str, goal_id: str, body: DonationGoalUpdate,
    _session: dict = Depends(require_auth),
) -> dict:
    updates = body.model_dump(exclude_none=True)
    result = await irl_repo.update_goal(channel, goal_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Goal not found")
    return result


@router.delete("/goals/{channel}/{goal_id}")
async def delete_goal(
    channel: str, goal_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await irl_repo.delete_goal(channel, goal_id)
    return {"status": "deleted"}


# ========== Question Queue ==========
@router.get("/questions/{channel}")
async def list_questions(
    channel: str,
    status: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await irl_repo.list_questions(channel, status)


@router.post("/questions/{channel}")
async def create_question(
    channel: str, body: QuestionCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await irl_repo.create_question(channel, body.username, body.question, body.priority)
    return result


@router.post("/questions/{channel}/{q_id}/status")
async def update_question_status(
    channel: str, q_id: str, status: str = Query(...),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await irl_repo.update_question_status(channel, q_id, status)
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    return result


@router.delete("/questions/{channel}/{q_id}")
async def delete_question(
    channel: str, q_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await irl_repo.delete_question(channel, q_id)
    return {"status": "deleted"}


# ========== Photo Requests ==========
@router.get("/photos/{channel}")
async def list_photo_requests(
    channel: str,
    status: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await irl_repo.list_photo_requests(channel, status)


@router.post("/photos/{channel}")
async def create_photo_request(
    channel: str, body: PhotoRequestCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await irl_repo.create_photo_request(channel, body.username, body.description, body.tip_amount)
    return result


@router.post("/photos/{channel}/{req_id}/status")
async def update_photo_request_status(
    channel: str, req_id: str, status: str = Query(...),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await irl_repo.update_photo_request_status(channel, req_id, status)
    if not result:
        raise HTTPException(status_code=404, detail="Photo request not found")
    return result


# ========== Challenge Wheel ==========
@router.get("/wheel/{channel}")
async def list_wheel_challenges(
    channel: str,
    unused_only: bool = Query(default=False),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await irl_repo.list_wheel_challenges(channel, unused_only)


@router.post("/wheel/{channel}")
async def add_wheel_challenge(
    channel: str, body: WheelChallengeCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await irl_repo.add_wheel_challenge(channel, body.challenge_text, body.username)
    return result


@router.post("/wheel/{channel}/spin")
async def spin_wheel(
    channel: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await irl_repo.spin_wheel(channel)
    if not result:
        raise HTTPException(status_code=400, detail="No unused challenges available")
    return result


@router.delete("/wheel/{channel}/{ch_id}")
async def delete_wheel_challenge(
    channel: str, ch_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await irl_repo.delete_wheel_challenge(channel, ch_id)
    return {"status": "deleted"}


# ========== Countdown Timer ==========
@router.get("/timers/{channel}")
async def list_timers(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await irl_repo.list_timers(channel)


@router.post("/timers/{channel}")
async def create_timer(
    channel: str, body: CountdownTimerCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await irl_repo.create_timer(channel, body.title, body.end_time, body.style)
    logger.info("Timer created for channel=%s: %s", channel, body.title)
    return result


@router.post("/timers/{channel}/{timer_id}/toggle")
async def toggle_timer(
    channel: str, timer_id: str, active: bool = Query(...),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await irl_repo.update_timer(channel, timer_id, active)
    if not result:
        raise HTTPException(status_code=404, detail="Timer not found")
    return result


@router.delete("/timers/{channel}/{timer_id}")
async def delete_timer(
    channel: str, timer_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await irl_repo.delete_timer(channel, timer_id)
    return {"status": "deleted"}
