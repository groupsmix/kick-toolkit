"""Giveaway system router."""

import random
from fastapi import APIRouter
from app.models.schemas import GiveawayCreate, GiveawayEntry
from app.services.database import giveaways, generate_id, now_iso

router = APIRouter(prefix="/api/giveaway", tags=["giveaway"])


@router.get("")
async def list_giveaways(channel: str = "") -> list[dict]:
    result = list(giveaways.values())
    if channel:
        result = [g for g in result if g["channel"] == channel]
    return sorted(result, key=lambda x: x["created_at"], reverse=True)


@router.post("/create")
async def create_giveaway(data: GiveawayCreate) -> dict:
    gw_id = generate_id()
    giveaway = {
        "id": gw_id,
        **data.model_dump(),
        "status": "active",
        "entries": [],
        "winner": None,
        "created_at": now_iso(),
        "ended_at": None,
    }
    giveaways[gw_id] = giveaway
    return giveaway


@router.get("/{giveaway_id}")
async def get_giveaway(giveaway_id: str) -> dict:
    if giveaway_id in giveaways:
        return giveaways[giveaway_id]
    return {"error": "Giveaway not found"}


@router.post("/{giveaway_id}/enter")
async def enter_giveaway(giveaway_id: str, entry: GiveawayEntry) -> dict:
    if giveaway_id not in giveaways:
        return {"error": "Giveaway not found"}

    gw = giveaways[giveaway_id]
    if gw["status"] != "active":
        return {"error": "Giveaway is not active"}

    if gw["max_entries"] and len(gw["entries"]) >= gw["max_entries"]:
        return {"error": "Giveaway is full"}

    existing = [e for e in gw["entries"] if e["username"].lower() == entry.username.lower()]
    if existing:
        return {"error": "Already entered"}

    entry_data = {"username": entry.username, "entered_at": now_iso()}
    gw["entries"].append(entry_data)
    return {"status": "entered", "entry": entry_data, "total_entries": len(gw["entries"])}


@router.post("/{giveaway_id}/roll")
async def roll_giveaway(giveaway_id: str) -> dict:
    if giveaway_id not in giveaways:
        return {"error": "Giveaway not found"}

    gw = giveaways[giveaway_id]
    if not gw["entries"]:
        return {"error": "No entries to roll from"}

    winner = random.choice(gw["entries"])
    gw["winner"] = winner["username"]
    gw["status"] = "completed"
    gw["ended_at"] = now_iso()

    return {"winner": winner["username"], "total_entries": len(gw["entries"]), "giveaway": gw}


@router.post("/{giveaway_id}/reroll")
async def reroll_giveaway(giveaway_id: str) -> dict:
    if giveaway_id not in giveaways:
        return {"error": "Giveaway not found"}

    gw = giveaways[giveaway_id]
    if not gw["entries"]:
        return {"error": "No entries to roll from"}

    previous_winner = gw["winner"]
    eligible = [e for e in gw["entries"] if e["username"] != previous_winner]
    if not eligible:
        eligible = gw["entries"]

    winner = random.choice(eligible)
    gw["winner"] = winner["username"]
    gw["status"] = "completed"

    return {"winner": winner["username"], "previous_winner": previous_winner, "total_entries": len(gw["entries"])}


@router.post("/{giveaway_id}/close")
async def close_giveaway(giveaway_id: str) -> dict:
    if giveaway_id not in giveaways:
        return {"error": "Giveaway not found"}

    gw = giveaways[giveaway_id]
    gw["status"] = "completed"
    gw["ended_at"] = now_iso()
    return gw


@router.delete("/{giveaway_id}")
async def delete_giveaway(giveaway_id: str) -> dict:
    if giveaway_id in giveaways:
        del giveaways[giveaway_id]
    return {"status": "deleted"}
