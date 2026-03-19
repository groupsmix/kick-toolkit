"""Chat logs router."""

from fastapi import APIRouter, Query
from typing import Optional
from app.models.schemas import ChatLogEntry
from app.services.database import chat_logs, generate_id, now_iso

router = APIRouter(prefix="/api/chatlogs", tags=["chatlogs"])


@router.get("")
async def get_chat_logs(
    channel: Optional[str] = None,
    username: Optional[str] = None,
    flagged_only: bool = False,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
) -> dict:
    filtered = chat_logs.copy()

    if channel:
        filtered = [l for l in filtered if l["channel"] == channel]
    if username:
        filtered = [l for l in filtered if l["username"].lower() == username.lower()]
    if flagged_only:
        filtered = [l for l in filtered if l["flagged"]]
    if search:
        search_lower = search.lower()
        filtered = [l for l in filtered if search_lower in l["message"].lower() or search_lower in l["username"].lower()]

    total = len(filtered)
    filtered = filtered[offset:offset + limit]

    return {"logs": filtered, "total": total, "limit": limit, "offset": offset}


@router.get("/user/{username}")
async def get_user_logs(username: str) -> dict:
    user_logs = [l for l in chat_logs if l["username"].lower() == username.lower()]
    total_messages = len(user_logs)
    flagged_messages = sum(1 for l in user_logs if l["flagged"])
    channels = list(set(l["channel"] for l in user_logs))

    return {
        "username": username,
        "total_messages": total_messages,
        "flagged_messages": flagged_messages,
        "channels": channels,
        "logs": user_logs[-100:],
    }


@router.post("")
async def add_chat_log(entry: ChatLogEntry) -> dict:
    log_entry = entry.model_dump()
    log_entry["id"] = generate_id()
    if not log_entry.get("timestamp"):
        log_entry["timestamp"] = now_iso()
    chat_logs.append(log_entry)
    return log_entry


@router.get("/stats/{channel}")
async def get_chat_stats(channel: str) -> dict:
    channel_logs = [l for l in chat_logs if l["channel"] == channel]
    total = len(channel_logs)
    flagged = sum(1 for l in channel_logs if l["flagged"])
    unique_users = len(set(l["username"] for l in channel_logs))
    top_chatters = {}
    for l in channel_logs:
        top_chatters[l["username"]] = top_chatters.get(l["username"], 0) + 1
    sorted_chatters = sorted(top_chatters.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "channel": channel,
        "total_messages": total,
        "flagged_messages": flagged,
        "unique_users": unique_users,
        "top_chatters": [{"username": u, "count": c} for u, c in sorted_chatters],
    }
