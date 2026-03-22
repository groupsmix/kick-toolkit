"""PostgreSQL database layer using psycopg 3 async."""

import json
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.services.schema import all_schemas

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Connection pool sizing — configurable via env vars
_POOL_MIN_SIZE = int(os.environ.get("DB_POOL_MIN_SIZE", "2"))
_POOL_MAX_SIZE = int(os.environ.get("DB_POOL_MAX_SIZE", "10"))

pool: Optional[AsyncConnectionPool] = None


async def init_pool():
    """Create the async connection pool."""
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL environment variable is required. "
            "Example: postgresql://user:pass@localhost:5432/dbname"
        )
    global pool
    pool = AsyncConnectionPool(
        conninfo=DATABASE_URL,
        min_size=_POOL_MIN_SIZE,
        max_size=_POOL_MAX_SIZE,
        kwargs={"row_factory": dict_row},
    )
    await pool.open()


async def close_pool():
    """Close the connection pool."""
    global pool
    if pool:
        await pool.close()
        pool = None


@asynccontextmanager
async def get_conn():
    """Get a connection from the pool."""
    if pool is None:
        raise RuntimeError("Database pool not initialised")
    async with pool.connection() as conn:
        yield conn


def _generate_id() -> str:
    """Generate a URL-safe random ID with 128 bits of entropy."""
    return secrets.token_urlsafe(16)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Schema — loaded from app/services/schema/ domain modules
# ---------------------------------------------------------------------------
# The monolithic SCHEMA_SQL that was here (~900 lines, 69 tables) has been
# split into 26 domain-specific modules under app/services/schema/.
# This re-export keeps backward compatibility for any code that imports it.
SCHEMA_SQL = all_schemas()


async def create_tables():
    """Create all tables if they don't exist."""
    async with get_conn() as conn:
        await conn.execute(all_schemas())
        await conn.commit()


DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() in ("true", "1", "yes")


async def seed_demo_data():
    """Populate demo data when DEMO_MODE is enabled and the database is empty."""
    if not DEMO_MODE:
        return

    async with get_conn() as conn:
        row = await conn.execute("SELECT count(*) AS cnt FROM chat_logs")
        result = await row.fetchone()
        if result and result["cnt"] > 0:
            return  # Already seeded

        channel = "demo_streamer"

        # Bot config
        await conn.execute(
            """INSERT INTO bot_configs (channel, prefix, enabled, welcome_message, auto_mod_enabled,
               welcome_enabled, welcome_new_message, welcome_returning_message, welcome_subscriber_message,
               shoutout_template, auto_shoutout_raiders)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            (channel, "!", True, "Welcome to the stream, {username}! Type !commands to see what I can do.", True,
             True,
             "Welcome to the stream, {username}! Enjoy your stay 🎉",
             "Welcome back, {username}! Great to see you again!",
             "Thank you for subscribing, {username}! You're amazing! 💜",
             "Check out {target} at kick.com/{target}! They were last playing {game}.",
             False),
        )

        # Timed messages
        timed_msgs = [
            (_generate_id(), channel, "Follow the stream to stay updated! Click the ❤️ button!", 15, True, _now_iso()),
            (_generate_id(), channel, "Join our Discord community! Link in the panels below.", 30, True, _now_iso()),
            (_generate_id(), channel, "Enjoying the stream? Share it with a friend!", 45, False, _now_iso()),
        ]
        for t in timed_msgs:
            await conn.execute(
                """INSERT INTO timed_messages (id, channel, message, interval_minutes, enabled, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                t,
            )

        # Bot commands
        commands = [
            (channel, "socials", "Follow me on Twitter and Instagram! Links in the panels below.", 30, True, False),
            (channel, "discord", "Join our Discord! Link in the panels below.", 30, True, False),
            (channel, "lurk", "{username} is now lurking! Enjoy the vibes.", 5, True, False),
            (channel, "ban", "Banned {target} from chat.", 0, True, True),
        ]
        for c in commands:
            await conn.execute(
                """INSERT INTO bot_commands (channel, name, response, cooldown, enabled, mod_only)
                   VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                c,
            )

        # Moderation rules
        rules = [
            (_generate_id(), channel, "Spam Filter", "spam", True, "delete", 2, json.dumps({"max_repeated_chars": 10, "max_emotes": 15})),
            (_generate_id(), channel, "Caps Lock Filter", "caps", True, "warn", 1, json.dumps({"max_caps_percent": 70, "min_length": 10})),
            (_generate_id(), channel, "Link Filter", "links", True, "delete", 2, json.dumps({"allow_clips": True, "allow_youtube": False})),
            (_generate_id(), channel, "Banned Words", "banned_words", True, "timeout", 3, json.dumps({"words": ["badword1", "badword2"]})),
            (_generate_id(), channel, "AI Toxicity Filter", "ai", True, "delete", 2, json.dumps({"threshold": 0.7})),
        ]
        for r in rules:
            await conn.execute(
                """INSERT INTO moderation_rules (id, channel, name, type, enabled, action, severity, settings)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                r,
            )

        # Chat logs
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
            ts = base_time + timedelta(minutes=i * 2)
            await conn.execute(
                """INSERT INTO chat_logs (id, channel, username, message, timestamp, flagged, flag_reason)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (_generate_id(), channel, username, message, ts.isoformat(), flagged, flag_reason),
            )

        # Giveaways
        now = _now_iso()
        gw_id = _generate_id()
        entries_completed = json.dumps([
            {"username": "viewer_andy", "entered_at": now},
            {"username": "sub_mike", "entered_at": now},
            {"username": "viewer_jenny", "entered_at": now},
            {"username": "new_viewer_1", "entered_at": now},
            {"username": "lurker_dave", "entered_at": now},
        ])
        await conn.execute(
            """INSERT INTO giveaways (id, title, channel, keyword, status, duration_seconds, max_entries,
               subscriber_only, follower_only, min_account_age_days, entries, winner, created_at, ended_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (gw_id, "Steam Gift Card Giveaway", channel, "!enter", "completed", 300, None,
             False, True, 0, entries_completed, "viewer_jenny", now, now),
        )

        gw_id2 = _generate_id()
        entries_active = json.dumps([
            {"username": "sub_mike", "entered_at": now},
            {"username": "viewer_andy", "entered_at": now},
        ])
        await conn.execute(
            """INSERT INTO giveaways (id, title, channel, keyword, status, duration_seconds, max_entries,
               subscriber_only, follower_only, min_account_age_days, entries, winner, created_at, ended_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (gw_id2, "Sub Emote Design Contest", channel, "!join", "active", 600, 50,
             True, False, 30, entries_active, None, now, None),
        )

        # Anti-alt settings
        await conn.execute(
            """INSERT INTO anti_alt_settings (id, enabled, min_account_age_days, auto_ban_threshold,
               auto_timeout_threshold, check_name_similarity, check_follow_status, whitelisted_users)
               VALUES (1, TRUE, 7, 80.0, 50.0, TRUE, TRUE, '[]') ON CONFLICT DO NOTHING""",
        )

        # Flagged accounts
        flagged = [
            ("xX_new_account_Xx", 87.5, "critical",
             json.dumps(["Account age < 1 day", "Username pattern match", "No followers", "Previously banned user similarity"]),
             0, 0, False, json.dumps(["banned_user_123", "banned_user_456"]), now),
            ("totally_not_alt", 62.0, "high",
             json.dumps(["Account age < 7 days", "Low follower count", "Name similarity to flagged user"]),
             3, 2, True, json.dumps(["banned_user_123"]), now),
            ("suspicious_viewer", 35.0, "medium",
             json.dumps(["Account age < 30 days", "Low engagement"]),
             15, 8, True, json.dumps([]), now),
        ]
        for f in flagged:
            await conn.execute(
                """INSERT INTO flagged_accounts (username, risk_score, risk_level, flags, account_age_days,
                   follower_count, is_following, similar_names, created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                f,
            )

        # Tournament
        t_id = _generate_id()
        participants = json.dumps([
            {"username": "player_1", "seed": 1, "eliminated": False},
            {"username": "player_2", "seed": 2, "eliminated": False},
            {"username": "player_3", "seed": 3, "eliminated": False},
            {"username": "player_4", "seed": 4, "eliminated": True},
            {"username": "player_5", "seed": 5, "eliminated": True},
            {"username": "player_6", "seed": 6, "eliminated": False},
            {"username": "player_7", "seed": 7, "eliminated": True},
            {"username": "player_8", "seed": 8, "eliminated": False},
        ])
        matches = json.dumps([
            {"id": _generate_id(), "round": 1, "match_number": 1, "player1": "player_1", "player2": "player_2", "winner": "player_1", "status": "completed"},
            {"id": _generate_id(), "round": 1, "match_number": 2, "player1": "player_3", "player2": "player_4", "winner": "player_3", "status": "completed"},
            {"id": _generate_id(), "round": 1, "match_number": 3, "player1": "player_5", "player2": "player_6", "winner": "player_6", "status": "completed"},
            {"id": _generate_id(), "round": 1, "match_number": 4, "player1": "player_7", "player2": "player_8", "winner": "player_8", "status": "completed"},
            {"id": _generate_id(), "round": 2, "match_number": 1, "player1": "player_1", "player2": "player_3", "winner": None, "status": "in_progress"},
            {"id": _generate_id(), "round": 2, "match_number": 2, "player1": "player_6", "player2": "player_8", "winner": None, "status": "pending"},
            {"id": _generate_id(), "round": 3, "match_number": 1, "player1": None, "player2": None, "winner": None, "status": "pending"},
        ])
        await conn.execute(
            """INSERT INTO tournaments (id, name, channel, game, max_participants, format, keyword,
               status, participants, matches, current_round, winner, created_at, started_at, ended_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (t_id, "Friday Night Fights", channel, "Street Fighter 6", 8, "single_elimination", "!join",
             "in_progress", participants, matches, 2, None, now, now, None),
        )

        # Saved ideas
        await conn.execute(
            """INSERT INTO saved_ideas (id, title, description, category, estimated_cost, engagement_level, requirements, saved)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (_generate_id(), "Sub-a-thon Milestone Rewards",
             "Set up tiered rewards for subscription milestones. At 50 subs do a challenge, at 100 subs give away a game, at 200 subs do a 24hr stream.",
             "experience", "$50-200", "high", json.dumps(["Subscription tracking", "Overlay setup"]), True),
        )

        # Marketplace seller profiles
        seller1_id = _generate_id()
        seller2_id = _generate_id()
        await conn.execute(
            """INSERT INTO seller_profiles
               (id, user_id, display_name, bio, avatar_url, website,
                total_sales, total_revenue, rating_avg, rating_count, status, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (seller1_id, "seller_user_1", "OverlayMaster", "Premium overlays and alert packs for Kick streamers.",
             None, "https://overlaymaster.design", 142, 2840.0, 4.8, 89, "active", now, now),
        )
        await conn.execute(
            """INSERT INTO seller_profiles
               (id, user_id, display_name, bio, avatar_url, website,
                total_sales, total_revenue, rating_avg, rating_count, status, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (seller2_id, "seller_user_2", "BotPresets Pro", "Custom chatbot configurations and widget skins.",
             None, None, 67, 670.0, 4.5, 34, "active", now, now),
        )

        # Marketplace items
        mp_items = [
            (seller1_id, "Neon Pulse Overlay Pack", "Complete streaming overlay set with animated alerts, webcam frames, and scene transitions. Neon cyberpunk theme.",
             "overlay", 14.99, json.dumps(["neon", "cyberpunk", "animated", "overlay"]), 87, 4.9, 52),
            (seller1_id, "Hype Alert Bundle", "Animated alert pack with subscriber, follower, and raid alerts. Includes sound effects.",
             "alert_pack", 9.99, json.dumps(["alerts", "animated", "sound", "subscriber"]), 55, 4.7, 37),
            (seller2_id, "Auto-Mod Command Pack", "Pre-configured chatbot commands for moderation, games, and engagement. 50+ commands included.",
             "chatbot_preset", 4.99, json.dumps(["chatbot", "commands", "moderation", "engagement"]), 45, 4.6, 22),
            (seller2_id, "Minimal Dark Widget Skin", "Clean dark-themed widget skin pack for chat, events, and goals.",
             "widget_skin", 7.99, json.dumps(["widget", "dark", "minimal", "clean"]), 22, 4.3, 12),
            (seller1_id, "Retro Arcade Overlay", "8-bit retro gaming overlay with pixel art frames and chiptune alerts.",
             "overlay", 12.99, json.dumps(["retro", "arcade", "pixel", "8bit"]), 0, 0.0, 0),
        ]
        for s_id, title, desc, cat, price, tags, downloads, rating, r_count in mp_items:
            await conn.execute(
                """INSERT INTO marketplace_items
                   (id, seller_id, title, description, category, price, tags,
                    status, download_count, rating_avg, rating_count, created_at, updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,'published',%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (_generate_id(), s_id, title, desc, cat, price, tags,
                 downloads, rating, r_count, now, now),
            )

        # ========== Stream Intelligence Sessions ==========
        intel_sessions = [
            (_generate_id(), channel, (base_time - timedelta(days=6)).isoformat(),
             (base_time - timedelta(days=6) + timedelta(hours=3, minutes=15)).isoformat(),
             195, 342, 287.5, 1845, 28, 5, 78.5, "Fortnite", "Solo ranked grind to Unreal"),
            (_generate_id(), channel, (base_time - timedelta(days=4)).isoformat(),
             (base_time - timedelta(days=4) + timedelta(hours=4)).isoformat(),
             240, 510, 415.0, 3200, 45, 12, 88.2, "Valorant", "Road to Immortal - Viewer games"),
            (_generate_id(), channel, (base_time - timedelta(days=2)).isoformat(),
             (base_time - timedelta(days=2) + timedelta(hours=2, minutes=30)).isoformat(),
             150, 220, 185.0, 980, 12, 2, 62.0, "Just Chatting", "AMA + Chill vibes"),
            (_generate_id(), channel, (base_time - timedelta(days=1)).isoformat(),
             (base_time - timedelta(days=1) + timedelta(hours=5)).isoformat(),
             300, 680, 520.0, 4500, 65, 18, 92.1, "Valorant", "Tournament practice w/ squad"),
            (_generate_id(), channel, base_time.isoformat(), None,
             0, 450, 380.0, 2100, 30, 8, 0.0, "Fortnite", "New season first look!"),
        ]
        for sid, ch, started, ended, dur, peak, avg_v, msgs, foll, subs, score, game, title in intel_sessions:
            await conn.execute(
                """INSERT INTO stream_intel_sessions
                   (id, channel, started_at, ended_at, duration_minutes, peak_viewers, avg_viewers,
                    chat_messages, new_followers, new_subscribers, stream_score, game, title)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (sid, ch, started, ended, dur, peak, avg_v, msgs, foll, subs, score, game, title),
            )

        # Stream score
        await conn.execute(
            """INSERT INTO stream_scores
               (channel, overall_score, viewer_score, chat_score, growth_score, consistency_score, trend, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (channel, 80.2, 75.0, 88.5, 82.0, 76.0, "rising", now),
        )

        # Best time slots
        best_times = [
            (channel, 1, 20, 25.0, 92.0, 1200, 45),  # Tuesday 8pm
            (channel, 3, 19, 30.0, 88.0, 1500, 52),  # Thursday 7pm
            (channel, 5, 21, 15.0, 95.0, 800, 28),   # Saturday 9pm
            (channel, 0, 20, 35.0, 78.0, 1800, 65),  # Monday 8pm
            (channel, 4, 18, 40.0, 72.0, 2000, 78),  # Friday 6pm
        ]
        for ch, dow, hr, comp, rec, avg_cat, active in best_times:
            await conn.execute(
                """INSERT INTO best_time_slots
                   (channel, day_of_week, hour, competition_score, recommended_score,
                    avg_category_viewers, active_streamers, updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (ch, dow, hr, comp, rec, avg_cat, active, now),
            )

        # ========== Viewer CRM ==========
        viewer_profiles = [
            (_generate_id(), channel, "viewer_andy", (base_time - timedelta(days=90)).isoformat(),
             base_time.isoformat(), 487, 45, True, True, "super_fan", 2700,
             json.dumps(["Valorant", "Fortnite"]), ""),
            (_generate_id(), channel, "sub_mike", (base_time - timedelta(days=180)).isoformat(),
             base_time.isoformat(), 1200, 82, True, True, "super_fan", 4920,
             json.dumps(["Valorant", "Just Chatting"]), "6-month sub streak"),
            (_generate_id(), channel, "viewer_jenny", (base_time - timedelta(days=60)).isoformat(),
             (base_time - timedelta(days=1)).isoformat(), 210, 28, False, True, "regular", 1680,
             json.dumps(["Fortnite"]), ""),
            (_generate_id(), channel, "mod_sarah", (base_time - timedelta(days=365)).isoformat(),
             base_time.isoformat(), 3500, 150, True, True, "super_fan", 9000,
             json.dumps(["Valorant", "Fortnite", "Just Chatting"]), "Head moderator"),
            (_generate_id(), channel, "lurker_dave", (base_time - timedelta(days=30)).isoformat(),
             (base_time - timedelta(days=14)).isoformat(), 12, 8, False, True, "at_risk", 480,
             json.dumps(["Just Chatting"]), ""),
            (_generate_id(), channel, "new_viewer_1", (base_time - timedelta(days=3)).isoformat(),
             base_time.isoformat(), 5, 2, False, False, "new", 60,
             json.dumps(["Fortnite"]), ""),
            (_generate_id(), channel, "new_viewer_2", (base_time - timedelta(days=2)).isoformat(),
             (base_time - timedelta(days=2)).isoformat(), 3, 1, False, True, "new", 30,
             json.dumps(["Fortnite"]), ""),
            (_generate_id(), channel, "old_regular_tom", (base_time - timedelta(days=120)).isoformat(),
             (base_time - timedelta(days=21)).isoformat(), 350, 40, False, True, "at_risk", 2400,
             json.dumps(["Valorant"]), "Used to be very active"),
        ]
        for vp in viewer_profiles:
            await conn.execute(
                """INSERT INTO viewer_profiles
                   (id, channel, username, first_seen, last_seen, total_messages, streams_watched,
                    is_subscriber, is_follower, segment, watch_time_minutes, favorite_games, notes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                vp,
            )

        # ========== AI Post-Stream Debrief ==========
        debrief_id = _generate_id()
        await conn.execute(
            """INSERT INTO debrief_results
               (id, channel, session_id, summary, top_moments, sentiment_timeline,
                chat_highlights, recommendations, title_suggestions, trending_topics, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (debrief_id, channel, intel_sessions[1][0],
             "Great 4-hour Valorant stream with strong viewer engagement. Chat was most active during "
             "competitive matches with peak participation at the 2-hour mark. Viewer sentiment was "
             "overwhelmingly positive (82% positive). The stream gained 45 new followers and 12 new "
             "subscribers, making it your best growth stream this week.",
             json.dumps([
                 {"minute": 45, "description": "Ace clutch in ranked", "intensity": 95},
                 {"minute": 120, "description": "Viewer games started - chat exploded", "intensity": 88},
                 {"minute": 195, "description": "Hit Immortal rank - celebration", "intensity": 92},
             ]),
             json.dumps([
                 {"minute": 0, "sentiment": 0.7, "label": "positive"},
                 {"minute": 30, "sentiment": 0.8, "label": "positive"},
                 {"minute": 60, "sentiment": 0.6, "label": "positive"},
                 {"minute": 90, "sentiment": 0.4, "label": "neutral"},
                 {"minute": 120, "sentiment": 0.9, "label": "very_positive"},
                 {"minute": 150, "sentiment": 0.85, "label": "positive"},
                 {"minute": 180, "sentiment": 0.75, "label": "positive"},
                 {"minute": 210, "sentiment": 0.92, "label": "very_positive"},
                 {"minute": 240, "sentiment": 0.88, "label": "positive"},
             ]),
             json.dumps([
                 "LETS GOOO ACE!", "This is the best stream ever", "IMMORTAL HYPE",
                 "viewer_andy gifted 5 subs!", "Chat was going crazy during viewer games",
             ]),
             json.dumps([
                 "Schedule more viewer game sessions - they drove 40% more engagement",
                 "Consider streaming Valorant ranked during Thursday evenings for best growth",
                 "Engage more during Just Chatting segments to maintain chat activity",
                 "Try a subathon during your next milestone celebration",
             ]),
             json.dumps([
                 "Road to Immortal: The Journey", "Ranked Grind + Viewer Games",
                 "Immortal achieved! What's next?",
             ]),
             json.dumps(["Valorant ranked", "viewer games", "rank up celebration"]),
             now),
        )

        # ========== Discord Bot Config ==========
        await conn.execute(
            """INSERT INTO discord_bot_configs
               (id, channel, guild_id, webhook_url, go_live_enabled, go_live_channel_id,
                go_live_message, chat_bridge_enabled, chat_bridge_channel_id,
                sub_sync_enabled, sub_sync_role_id, stats_commands_enabled,
                schedule_display_enabled, schedule_channel_id, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (_generate_id(), channel, "123456789012345678",
             "https://discord.com/api/webhooks/example/token",
             True, "987654321098765432",
             "{streamer} is now live on Kick! Playing {game} - {title}",
             False, "", False, "", True, True, "111222333444555666", now),
        )

        # ========== Revenue Entries ==========
        revenue_data = [
            (_generate_id(), channel, "subscription", 49.95, "USD", "Monthly subs (10 x $4.99)",
             None, (base_time - timedelta(days=30)).strftime("%Y-%m-%d")),
            (_generate_id(), channel, "subscription", 74.85, "USD", "Monthly subs (15 x $4.99)",
             None, (base_time - timedelta(days=0)).strftime("%Y-%m-%d")),
            (_generate_id(), channel, "tip", 25.00, "USD", "Tip from sub_mike",
             intel_sessions[1][0], (base_time - timedelta(days=4)).strftime("%Y-%m-%d")),
            (_generate_id(), channel, "tip", 50.00, "USD", "Tip from viewer_andy",
             intel_sessions[3][0], (base_time - timedelta(days=1)).strftime("%Y-%m-%d")),
            (_generate_id(), channel, "sponsor", 500.00, "USD", "GamerSupps sponsorship - March",
             None, (base_time - timedelta(days=15)).strftime("%Y-%m-%d")),
            (_generate_id(), channel, "merch", 120.00, "USD", "T-shirt sales (6 units)",
             None, (base_time - timedelta(days=10)).strftime("%Y-%m-%d")),
            (_generate_id(), channel, "tip", 10.00, "USD", "Tip from new_viewer_1",
             intel_sessions[4][0], base_time.strftime("%Y-%m-%d")),
            (_generate_id(), channel, "subscription", 39.92, "USD", "Monthly subs (8 x $4.99)",
             None, (base_time - timedelta(days=60)).strftime("%Y-%m-%d")),
            (_generate_id(), channel, "sponsor", 300.00, "USD", "Energy drink promo - Feb",
             None, (base_time - timedelta(days=45)).strftime("%Y-%m-%d")),
        ]
        for rv in revenue_data:
            await conn.execute(
                """INSERT INTO revenue_entries
                   (id, channel, source, amount, currency, description, stream_session_id, date, created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (*rv, now),
            )

        # ========== Highlight Markers ==========
        highlights = [
            (_generate_id(), channel, intel_sessions[1][0], 2700, 95.0, 12.5, 30,
             "ACE CLUTCH! Chat went absolutely wild",
             json.dumps(["LETS GOOO", "ACE!!", "NO WAY", "INSANE", "clip it!!!"]), "hype"),
            (_generate_id(), channel, intel_sessions[1][0], 7200, 88.0, 10.2, 45,
             "Viewer games started - massive chat spike",
             json.dumps(["pick me!", "!join", "viewer games HYPE", "finally!", "lets play"]), "hype"),
            (_generate_id(), channel, intel_sessions[1][0], 11700, 92.0, 15.0, 60,
             "Hit Immortal rank - celebration moment",
             json.dumps(["IMMORTAL", "HE DID IT", "LETS GOOO", "GG", "POGGERS"]), "clutch"),
            (_generate_id(), channel, intel_sessions[3][0], 5400, 85.0, 9.8, 25,
             "1v5 clutch in tournament practice",
             json.dumps(["CLUTCH GOD", "HOW??", "insane play", "pro level"]), "clutch"),
            (_generate_id(), channel, intel_sessions[3][0], 12600, 78.0, 8.0, 20,
             "Funny fail moment - fell off map",
             json.dumps(["LMAOOO", "BRO WHAT", "hahaha", "clip that", "fail"]), "funny"),
        ]
        for hl in highlights:
            await conn.execute(
                """INSERT INTO highlight_markers
                   (id, channel, session_id, timestamp_offset_seconds, intensity, message_rate,
                    duration_seconds, description, sample_messages, category, created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (*hl, now),
            )

        # ========== Phase 2: Chat Polls ==========
        poll1_id = _generate_id()
        poll2_id = _generate_id()
        await conn.execute(
            """INSERT INTO polls (id, channel, title, options, duration_seconds, allow_multiple_votes, status, created_at, closed_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (poll1_id, channel, "What game should we play next?",
             json.dumps(["Valorant", "Fortnite", "Minecraft", "Just Chatting"]),
             300, False, "active", now, None),
        )
        await conn.execute(
            """INSERT INTO polls (id, channel, title, options, duration_seconds, allow_multiple_votes, status, created_at, closed_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (poll2_id, channel, "Best stream moment this week?",
             json.dumps(["Monday clutch", "Wednesday raid", "Friday subathon"]),
             600, False, "closed", (base_time - timedelta(days=2)).isoformat(),
             (base_time - timedelta(days=2) + timedelta(hours=1)).isoformat()),
        )
        poll_voters = ["viewer_andy", "sub_mike", "viewer_jenny", "mod_sarah", "new_viewer_1"]
        for i, voter in enumerate(poll_voters):
            await conn.execute(
                """INSERT INTO poll_votes (id, poll_id, channel, username, option_index, voted_at)
                   VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (_generate_id(), poll1_id, channel, voter, i % 4, now),
            )
        for i, voter in enumerate(poll_voters[:3]):
            await conn.execute(
                """INSERT INTO poll_votes (id, poll_id, channel, username, option_index, voted_at)
                   VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (_generate_id(), poll2_id, channel, voter, i % 3,
                 (base_time - timedelta(days=2)).isoformat()),
            )

        # ========== Phase 2: Predictions ==========
        pred1_id = _generate_id()
        pred2_id = _generate_id()
        await conn.execute(
            """INSERT INTO predictions (id, channel, title, outcomes, lock_seconds, status, winning_index, created_at, locked_at, resolved_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (pred1_id, channel, "Will we win the next ranked match?",
             json.dumps(["Yes - EZ win", "No - tough lobby"]),
             300, "open", None, now, None, None),
        )
        await conn.execute(
            """INSERT INTO predictions (id, channel, title, outcomes, lock_seconds, status, winning_index, created_at, locked_at, resolved_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (pred2_id, channel, "How many kills in the next game?",
             json.dumps(["0-5 kills", "6-10 kills", "11+ kills"]),
             600, "resolved", 1, (base_time - timedelta(days=1)).isoformat(),
             (base_time - timedelta(hours=23, minutes=30)).isoformat(),
             (base_time - timedelta(hours=23)).isoformat()),
        )
        pred_bettors = [
            ("viewer_andy", 0, 100), ("sub_mike", 0, 250),
            ("mod_sarah", 1, 150), ("viewer_jenny", 0, 50),
        ]
        for username, outcome_idx, amount in pred_bettors:
            await conn.execute(
                """INSERT INTO prediction_bets (id, prediction_id, channel, username, outcome_index, amount, status, payout, created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (_generate_id(), pred1_id, channel, username, outcome_idx, amount, "pending", 0, now),
            )

        # ========== Phase 2: Translation Settings ==========
        await conn.execute(
            """INSERT INTO translation_settings (channel, enabled, target_language, auto_translate, show_original, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (channel, True, "en", False, True, now),
        )

        await conn.commit()
