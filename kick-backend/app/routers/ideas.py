"""Stream giveaway ideas generator router."""

import logging
import random

from fastapi import APIRouter, Depends

from app.dependencies import require_auth
from app.models.schemas import GiveawayIdea, IdeaGenerateRequest
from app.repositories import ideas as ideas_repo
from app.services.db import _generate_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ideas", tags=["ideas"])

# Idea templates database
IDEA_TEMPLATES = [
    {"title": "Custom Merch Drop", "description": "Design and give away custom merchandise like t-shirts, hoodies, or stickers with your brand. Use a keyword entry system where viewers type !merch to enter.", "category": "physical", "estimated_cost": "$20-50", "engagement_level": "high", "requirements": ["Merch supplier", "Shipping logistics"]},
    {"title": "Gaming Peripheral Giveaway", "description": "Give away a gaming mouse, keyboard, or headset. Partner with a brand for sponsorship or buy one yourself. Great for milestone celebrations.", "category": "physical", "estimated_cost": "$50-150", "engagement_level": "high", "requirements": ["Budget for hardware", "Sponsor contact (optional)"]},
    {"title": "Snack Box Surprise", "description": "Send a mystery snack box from another country to the winner. Fun unboxing content and great viewer engagement.", "category": "physical", "estimated_cost": "$25-40", "engagement_level": "medium", "requirements": ["International shipping", "Snack box service subscription"]},
    {"title": "Steam Gift Card Raffle", "description": "Classic giveaway - give away Steam gift cards. Viewers enter by typing a keyword. Scale the amount based on viewer count milestones.", "category": "digital", "estimated_cost": "$10-50", "engagement_level": "high", "requirements": ["Gift card purchase"]},
    {"title": "Game Key Drop", "description": "Give away game keys from Humble Bundle or other sources. Can do multiple smaller giveaways throughout the stream to keep engagement up.", "category": "digital", "estimated_cost": "$5-30", "engagement_level": "medium", "requirements": ["Game keys source"]},
    {"title": "Discord Nitro Giveaway", "description": "Give away Discord Nitro subscriptions. Great for building your Discord community as viewers will join to claim.", "category": "digital", "estimated_cost": "$10-100", "engagement_level": "medium", "requirements": ["Discord server"]},
    {"title": "Custom Emote/Avatar Commission", "description": "Commission a custom emote or avatar for the winner from a digital artist. Unique prize that viewers really value.", "category": "digital", "estimated_cost": "$15-50", "engagement_level": "high", "requirements": ["Artist contact", "Turnaround time agreement"]},
    {"title": "Play With The Streamer", "description": "Winner gets to play games with you on stream. Can be a ranked duo, casual session, or coaching. Zero cost, maximum engagement.", "category": "experience", "estimated_cost": "Free", "engagement_level": "high", "requirements": ["Time slot in stream", "Game compatibility"]},
    {"title": "Custom Shoutout Stream", "description": "Dedicate a segment of your stream to the winner - raid their channel, promote their socials, play their content.", "category": "experience", "estimated_cost": "Free", "engagement_level": "medium", "requirements": ["Stream segment planning"]},
    {"title": "Sub-a-thon Milestone Rewards", "description": "Set up tiered rewards for subscription milestones. At 50 subs do a challenge, at 100 subs give away a game, at 200 subs do a 24hr stream.", "category": "experience", "estimated_cost": "$50-200", "engagement_level": "high", "requirements": ["Subscription tracking", "Overlay setup"]},
    {"title": "1-on-1 Coaching Session", "description": "Offer a private coaching session in your main game to the winner. High value, zero cost, and positions you as an expert.", "category": "experience", "estimated_cost": "Free", "engagement_level": "high", "requirements": ["Scheduling system", "VOD review setup (optional)"]},
    {"title": "In-Game Currency/Items Drop", "description": "Give away in-game currency, skins, or items. Works great for games with tradeable items. Entry via chat keyword during gameplay.", "category": "in-game", "estimated_cost": "$5-50", "engagement_level": "high", "requirements": ["Game with tradeable items", "Trade system knowledge"]},
    {"title": "Carry/Boost Service", "description": "Offer to carry the winner through a difficult game challenge - raid boss, ranked climb, achievement unlock.", "category": "in-game", "estimated_cost": "Free", "engagement_level": "high", "requirements": ["Skill in the game", "Time commitment"]},
    {"title": "Custom In-Game Build/Setup", "description": "Create a custom character build, base design, or setup for the winner in a builder/survival game.", "category": "in-game", "estimated_cost": "Free", "engagement_level": "medium", "requirements": ["Game with creative elements"]},
    {"title": "Kick Sub Bomb", "description": "Gift multiple subscriptions to random viewers. Creates massive hype in chat and encourages community growth.", "category": "subscription", "estimated_cost": "$25-100", "engagement_level": "high", "requirements": ["Kick gifted sub support"]},
    {"title": "Streaming Service Giveaway", "description": "Give away a month of Netflix, Spotify Premium, or another streaming service. Universally appealing prize.", "category": "subscription", "estimated_cost": "$10-15", "engagement_level": "medium", "requirements": ["Gift card availability"]},
    {"title": "VIP Chat Badge Contest", "description": "Award VIP status or special chat badges to contest winners. Costs nothing but creates exclusivity and drives engagement.", "category": "subscription", "estimated_cost": "Free", "engagement_level": "high", "requirements": ["VIP/badge system on Kick"]},
    {"title": "Community Challenge Rewards", "description": "Set community goals (chat messages, follows, subs) and reward the whole chat when milestones are hit with group giveaways.", "category": "experience", "estimated_cost": "$0-100", "engagement_level": "high", "requirements": ["Milestone tracking", "Group reward system"]},
]


@router.post("/generate")
async def generate_ideas(req: IdeaGenerateRequest) -> list[dict]:
    pool = IDEA_TEMPLATES.copy()

    if req.category:
        pool = [i for i in pool if i["category"] == req.category]

    if req.budget:
        budget_lower = req.budget.lower()
        if budget_lower == "free":
            pool = [i for i in pool if "Free" in i["estimated_cost"] or "$0" in i["estimated_cost"]]
        elif budget_lower == "low":
            pool = [i for i in pool if "Free" in i["estimated_cost"] or any(c in i["estimated_cost"] for c in ["$5", "$10", "$15", "$20", "$25"])]

    if not pool:
        pool = IDEA_TEMPLATES.copy()

    selected = random.sample(pool, min(5, len(pool)))

    return [{"id": _generate_id(), **idea, "saved": False} for idea in selected]


@router.get("/saved")
async def get_saved_ideas(_session: dict = Depends(require_auth)) -> list[dict]:
    return await ideas_repo.list_saved()


@router.post("/save")
async def save_idea(idea: GiveawayIdea, _session: dict = Depends(require_auth)) -> dict:
    result = await ideas_repo.save_idea(
        idea.title, idea.description, idea.category,
        idea.estimated_cost, idea.engagement_level, idea.requirements,
    )
    logger.info("Idea '%s' saved", idea.title)
    return result


@router.delete("/saved/{idea_id}")
async def delete_saved_idea(idea_id: str, _session: dict = Depends(require_auth)) -> dict:
    await ideas_repo.delete_saved(idea_id)
    return {"status": "deleted"}


@router.get("/categories")
async def get_categories() -> list[dict]:
    return [
        {"value": "physical", "label": "Physical Prizes", "icon": "package", "count": len([i for i in IDEA_TEMPLATES if i["category"] == "physical"])},
        {"value": "digital", "label": "Digital Prizes", "icon": "download", "count": len([i for i in IDEA_TEMPLATES if i["category"] == "digital"])},
        {"value": "experience", "label": "Experiences", "icon": "star", "count": len([i for i in IDEA_TEMPLATES if i["category"] == "experience"])},
        {"value": "in-game", "label": "In-Game Items", "icon": "gamepad", "count": len([i for i in IDEA_TEMPLATES if i["category"] == "in-game"])},
        {"value": "subscription", "label": "Subscriptions", "icon": "credit-card", "count": len([i for i in IDEA_TEMPLATES if i["category"] == "subscription"])},
    ]
