"""In-memory database for the Kick Toolkit demo."""

import uuid
from datetime import datetime, timezone
from typing import Optional


def generate_id() -> str:
    return str(uuid.uuid4())[:8]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ========== In-Memory Storage ==========

bot_configs: dict[str, dict] = {}
bot_commands: dict[str, list[dict]] = {}
moderation_rules: dict[str, list[dict]] = {}
chat_logs: list[dict] = []
giveaways: dict[str, dict] = {}
anti_alt_settings: dict = {
    "enabled": True,
    "min_account_age_days": 7,
    "auto_ban_threshold": 80.0,
    "auto_timeout_threshold": 50.0,
    "check_name_similarity": True,
    "check_follow_status": True,
    "whitelisted_users": [],
}
flagged_accounts: list[dict] = []
tournaments: dict[str, dict] = {}
saved_ideas: list[dict] = []


# Seed some demo data
def seed_demo_data():
    """Populate with realistic demo data."""
    channel = "demo_streamer"

    # Seed bot config
    bot_configs[channel] = {
        "channel": channel,
        "prefix": "!",
        "enabled": True,
        "welcome_message": "Welcome to the stream, {username}! Type !commands to see what I can do.",
        "auto_mod_enabled": True,
    }

    # Seed bot commands
    bot_commands[channel] = [
        {"name": "socials", "response": "Follow me on Twitter @demo_streamer and Instagram @demo_streamer!", "cooldown": 30, "enabled": True, "mod_only": False},
        {"name": "discord", "response": "Join our Discord: https://discord.gg/example", "cooldown": 30, "enabled": True, "mod_only": False},
        {"name": "rank", "response": "Current rank: Diamond 2 | Peak: Master", "cooldown": 10, "enabled": True, "mod_only": False},
        {"name": "lurk", "response": "{username} is now lurking! Enjoy the vibes.", "cooldown": 5, "enabled": True, "mod_only": False},
        {"name": "ban", "response": "Banned {target} from chat.", "cooldown": 0, "enabled": True, "mod_only": True},
    ]

    # Seed moderation rules
    moderation_rules[channel] = [
        {"id": generate_id(), "name": "Spam Filter", "type": "spam", "enabled": True, "action": "delete", "severity": 2, "settings": {"max_repeated_chars": 10, "max_emotes": 15}},
        {"id": generate_id(), "name": "Caps Lock Filter", "type": "caps", "enabled": True, "action": "warn", "severity": 1, "settings": {"max_caps_percent": 70, "min_length": 10}},
        {"id": generate_id(), "name": "Link Filter", "type": "links", "enabled": True, "action": "delete", "severity": 2, "settings": {"allow_clips": True, "allow_youtube": False}},
        {"id": generate_id(), "name": "Banned Words", "type": "banned_words", "enabled": True, "action": "timeout", "severity": 3, "settings": {"words": ["badword1", "badword2"]}},
        {"id": generate_id(), "name": "AI Toxicity Filter", "type": "ai", "enabled": True, "action": "delete", "severity": 2, "settings": {"threshold": 0.7}},
    ]

    # Seed chat logs
    demo_messages = [
        ("viewer_andy", "Hey everyone! Hyped for the stream!", False, None),
        ("mod_sarah", "Welcome to the stream folks! Rules are in the panel below.", False, None),
        ("toxic_tim", "This gameplay is absolutely garbage lmao get good", True, "AI: Toxicity detected (0.82)"),
        ("new_viewer_1", "First time here, what game is this?", False, None),
        ("viewer_andy", "!rank", False, None),
        ("sub_mike", "Just resubbed for 6 months! Love the content", False, None),
        ("spam_bot_99", "FREE VIEWERS AT bit.ly/scam123 FREE VIEWERS", True, "Link spam detected"),
        ("viewer_jenny", "Can you play ranked next?", False, None),
        ("caps_carl", "LETS GOOOOOOOO THAT WAS INSANE PLAY HOLY", True, "Excessive caps (85%)"),
        ("mod_sarah", "!ban spam_bot_99", False, None),
        ("viewer_andy", "GG! That was so close", False, None),
        ("new_viewer_2", "Followed! This is really entertaining", False, None),
        ("sub_mike", "!discord", False, None),
        ("viewer_jenny", "When is the next giveaway?", False, None),
        ("lurker_dave", "!lurk", False, None),
    ]

    base_time = datetime(2026, 3, 18, 19, 0, 0, tzinfo=timezone.utc)
    for i, (username, message, flagged, flag_reason) in enumerate(demo_messages):
        from datetime import timedelta
        ts = base_time + timedelta(minutes=i * 2)
        chat_logs.append({
            "id": generate_id(),
            "channel": channel,
            "username": username,
            "message": message,
            "timestamp": ts.isoformat(),
            "flagged": flagged,
            "flag_reason": flag_reason,
        })

    # Seed a completed giveaway
    gw_id = generate_id()
    giveaways[gw_id] = {
        "id": gw_id,
        "title": "Steam Gift Card Giveaway",
        "channel": channel,
        "keyword": "!enter",
        "status": "completed",
        "duration_seconds": 300,
        "max_entries": None,
        "subscriber_only": False,
        "follower_only": True,
        "min_account_age_days": 0,
        "entries": [
            {"username": "viewer_andy", "entered_at": now_iso()},
            {"username": "sub_mike", "entered_at": now_iso()},
            {"username": "viewer_jenny", "entered_at": now_iso()},
            {"username": "new_viewer_1", "entered_at": now_iso()},
            {"username": "lurker_dave", "entered_at": now_iso()},
        ],
        "winner": "viewer_jenny",
        "created_at": now_iso(),
        "ended_at": now_iso(),
    }

    # Seed an active giveaway
    gw_id2 = generate_id()
    giveaways[gw_id2] = {
        "id": gw_id2,
        "title": "Sub Emote Design Contest",
        "channel": channel,
        "keyword": "!join",
        "status": "active",
        "duration_seconds": 600,
        "max_entries": 50,
        "subscriber_only": True,
        "follower_only": False,
        "min_account_age_days": 30,
        "entries": [
            {"username": "sub_mike", "entered_at": now_iso()},
            {"username": "viewer_andy", "entered_at": now_iso()},
        ],
        "winner": None,
        "created_at": now_iso(),
        "ended_at": None,
    }

    # Seed flagged alt accounts
    flagged_accounts.extend([
        {
            "username": "xX_new_account_Xx",
            "risk_score": 87.5,
            "risk_level": "critical",
            "flags": ["Account age < 1 day", "Username pattern match", "No followers", "Previously banned user similarity"],
            "account_age_days": 0,
            "follower_count": 0,
            "is_following": False,
            "similar_names": ["banned_user_123", "banned_user_456"],
            "created_at": now_iso(),
        },
        {
            "username": "totally_not_alt",
            "risk_score": 62.0,
            "risk_level": "high",
            "flags": ["Account age < 7 days", "Low follower count", "Name similarity to flagged user"],
            "account_age_days": 3,
            "follower_count": 2,
            "is_following": True,
            "similar_names": ["banned_user_123"],
            "created_at": now_iso(),
        },
        {
            "username": "suspicious_viewer",
            "risk_score": 35.0,
            "risk_level": "medium",
            "flags": ["Account age < 30 days", "Low engagement"],
            "account_age_days": 15,
            "follower_count": 8,
            "is_following": True,
            "similar_names": [],
            "created_at": now_iso(),
        },
    ])

    # Seed a tournament
    t_id = generate_id()
    participants = [
        {"username": "player_1", "seed": 1, "eliminated": False},
        {"username": "player_2", "seed": 2, "eliminated": False},
        {"username": "player_3", "seed": 3, "eliminated": False},
        {"username": "player_4", "seed": 4, "eliminated": True},
        {"username": "player_5", "seed": 5, "eliminated": True},
        {"username": "player_6", "seed": 6, "eliminated": False},
        {"username": "player_7", "seed": 7, "eliminated": True},
        {"username": "player_8", "seed": 8, "eliminated": False},
    ]
    matches = [
        {"id": generate_id(), "round": 1, "match_number": 1, "player1": "player_1", "player2": "player_2", "winner": "player_1", "status": "completed"},
        {"id": generate_id(), "round": 1, "match_number": 2, "player1": "player_3", "player2": "player_4", "winner": "player_3", "status": "completed"},
        {"id": generate_id(), "round": 1, "match_number": 3, "player1": "player_5", "player2": "player_6", "winner": "player_6", "status": "completed"},
        {"id": generate_id(), "round": 1, "match_number": 4, "player1": "player_7", "player2": "player_8", "winner": "player_8", "status": "completed"},
        {"id": generate_id(), "round": 2, "match_number": 1, "player1": "player_1", "player2": "player_3", "winner": None, "status": "in_progress"},
        {"id": generate_id(), "round": 2, "match_number": 2, "player1": "player_6", "player2": "player_8", "winner": None, "status": "pending"},
        {"id": generate_id(), "round": 3, "match_number": 1, "player1": None, "player2": None, "winner": None, "status": "pending"},
    ]
    tournaments[t_id] = {
        "id": t_id,
        "name": "Friday Night Fights",
        "channel": channel,
        "game": "Street Fighter 6",
        "max_participants": 8,
        "format": "single_elimination",
        "keyword": "!join",
        "status": "in_progress",
        "participants": participants,
        "matches": matches,
        "current_round": 2,
        "winner": None,
        "created_at": now_iso(),
        "started_at": now_iso(),
        "ended_at": None,
    }

    # Seed saved ideas
    saved_ideas.extend([
        {
            "id": generate_id(),
            "title": "Sub-a-thon Milestone Rewards",
            "description": "Set up tiered rewards for subscription milestones. At 50 subs do a challenge, at 100 subs give away a game, at 200 subs do a 24hr stream.",
            "category": "experience",
            "estimated_cost": "$50-200",
            "engagement_level": "high",
            "requirements": ["Subscription tracking", "Overlay setup"],
            "saved": True,
        },
    ])


# Initialize demo data on import
seed_demo_data()
