"""Loyalty & Points System router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import LoyaltySettingsUpdate, LoyaltyRewardCreate, LoyaltyRedeemRequest, PointsAdjustRequest
from app.repositories import loyalty as loyalty_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/loyalty", tags=["loyalty"])


@router.get("/settings/{channel}")
async def get_settings(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    settings = await loyalty_repo.get_settings(channel)
    if settings:
        return settings
    return {
        "channel": channel, "enabled": True, "points_name": "Points",
        "points_per_message": 1, "points_per_minute_watched": 2,
        "bonus_subscriber_multiplier": 2.0, "bonus_follower_multiplier": 1.5,
        "daily_bonus": 50,
    }


@router.put("/settings/{channel}")
async def update_settings(
    channel: str, body: LoyaltySettingsUpdate, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    result = await loyalty_repo.upsert_settings(
        channel=channel,
        enabled=body.enabled,
        points_name=body.points_name,
        points_per_message=body.points_per_message,
        points_per_minute_watched=body.points_per_minute_watched,
        bonus_subscriber_multiplier=body.bonus_subscriber_multiplier,
        bonus_follower_multiplier=body.bonus_follower_multiplier,
        daily_bonus=body.daily_bonus,
    )
    logger.info("Loyalty settings updated for channel=%s", channel)
    return result


@router.get("/leaderboard/{channel}")
async def get_leaderboard(
    channel: str,
    limit: int = Query(default=20, le=100),
    session: dict = Depends(require_auth),
) -> list[dict]:
    require_channel_owner(session, channel)
    return await loyalty_repo.get_leaderboard(channel, limit)


@router.get("/points/{channel}/{username}")
async def get_user_points(
    channel: str, username: str, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    points = await loyalty_repo.get_user_points(channel, username)
    if points:
        return points
    return {"username": username, "channel": channel, "balance": 0, "total_earned": 0, "total_spent": 0}


@router.post("/points/{channel}/adjust")
async def adjust_points(
    channel: str, body: PointsAdjustRequest, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    result = await loyalty_repo.adjust_points(channel, body.username, body.amount)
    logger.info("Points adjusted for %s in channel=%s: %+d (%s)", body.username, channel, body.amount, body.reason)
    return result


@router.get("/rewards/{channel}")
async def list_rewards(channel: str, session: dict = Depends(require_auth)) -> list[dict]:
    require_channel_owner(session, channel)
    return await loyalty_repo.list_rewards(channel)


@router.post("/rewards/{channel}")
async def create_reward(
    channel: str, body: LoyaltyRewardCreate, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    result = await loyalty_repo.create_reward(
        channel=channel, name=body.name, description=body.description,
        cost=body.cost, reward_type=body.type, enabled=body.enabled,
        max_redemptions=body.max_redemptions,
    )
    logger.info("Reward '%s' created for channel=%s", body.name, channel)
    return result


@router.delete("/rewards/{channel}/{reward_id}")
async def delete_reward(
    channel: str, reward_id: str, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    await loyalty_repo.delete_reward(channel, reward_id)
    return {"status": "deleted"}


@router.post("/redeem/{channel}")
async def redeem_reward(
    channel: str, body: LoyaltyRedeemRequest, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    result = await loyalty_repo.redeem_reward(channel, body.username, body.reward_id)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot redeem reward. Check balance, availability, and reward status.")
    logger.info("Reward redeemed by %s in channel=%s", body.username, channel)
    return result


@router.get("/redemptions/{channel}")
async def list_redemptions(
    channel: str,
    limit: int = Query(default=50, le=200),
    session: dict = Depends(require_auth),
) -> list[dict]:
    require_channel_owner(session, channel)
    return await loyalty_repo.list_redemptions(channel, limit)
