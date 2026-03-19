"""PostgreSQL database layer using psycopg 3 async."""

import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://kicktools:kicktools@localhost:5432/kicktools",
)

pool: Optional[AsyncConnectionPool] = None


async def init_pool():
    """Create the async connection pool."""
    global pool
    pool = AsyncConnectionPool(
        conninfo=DATABASE_URL,
        min_size=2,
        max_size=10,
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
    return str(uuid.uuid4())[:8]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS bot_configs (
    channel TEXT PRIMARY KEY,
    prefix TEXT NOT NULL DEFAULT '!',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    welcome_message TEXT,
    auto_mod_enabled BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS bot_commands (
    id SERIAL PRIMARY KEY,
    channel TEXT NOT NULL,
    name TEXT NOT NULL,
    response TEXT NOT NULL,
    cooldown INT NOT NULL DEFAULT 5,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    mod_only BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(channel, name)
);

CREATE TABLE IF NOT EXISTS moderation_rules (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    action TEXT NOT NULL DEFAULT 'delete',
    severity INT NOT NULL DEFAULT 1,
    settings JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS chat_logs (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    username TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    flagged BOOLEAN NOT NULL DEFAULT FALSE,
    flag_reason TEXT
);

CREATE TABLE IF NOT EXISTS giveaways (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    channel TEXT NOT NULL,
    keyword TEXT NOT NULL DEFAULT '!enter',
    status TEXT NOT NULL DEFAULT 'active',
    duration_seconds INT NOT NULL DEFAULT 300,
    max_entries INT,
    subscriber_only BOOLEAN NOT NULL DEFAULT FALSE,
    follower_only BOOLEAN NOT NULL DEFAULT FALSE,
    min_account_age_days INT NOT NULL DEFAULT 0,
    entries JSONB NOT NULL DEFAULT '[]',
    winner TEXT,
    created_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS anti_alt_settings (
    id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    min_account_age_days INT NOT NULL DEFAULT 7,
    auto_ban_threshold FLOAT NOT NULL DEFAULT 80.0,
    auto_timeout_threshold FLOAT NOT NULL DEFAULT 50.0,
    check_name_similarity BOOLEAN NOT NULL DEFAULT TRUE,
    check_follow_status BOOLEAN NOT NULL DEFAULT TRUE,
    whitelisted_users JSONB NOT NULL DEFAULT '[]',
    challenge_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    challenge_type TEXT NOT NULL DEFAULT 'follow',
    challenge_wait_minutes INT NOT NULL DEFAULT 10,
    challenge_message TEXT NOT NULL DEFAULT 'Please follow the channel and wait {minutes} minutes before chatting.',
    auto_whitelist_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    auto_whitelist_min_messages INT NOT NULL DEFAULT 100,
    auto_whitelist_min_follow_days INT NOT NULL DEFAULT 30
);

CREATE TABLE IF NOT EXISTS flagged_accounts (
    username TEXT PRIMARY KEY,
    risk_score FLOAT NOT NULL,
    risk_level TEXT NOT NULL,
    flags JSONB NOT NULL DEFAULT '[]',
    account_age_days INT NOT NULL DEFAULT 0,
    follower_count INT NOT NULL DEFAULT 0,
    is_following BOOLEAN NOT NULL DEFAULT FALSE,
    similar_names JSONB NOT NULL DEFAULT '[]',
    fingerprint_match_count INT NOT NULL DEFAULT 0,
    behavior_similarity_score FLOAT NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS banned_users (
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    banned_at TEXT NOT NULL,
    ban_reason TEXT,
    ban_source TEXT NOT NULL DEFAULT 'manual',
    PRIMARY KEY (username, channel)
);

CREATE TABLE IF NOT EXISTS user_fingerprints (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    fingerprint_hash TEXT,
    client_ip_hash TEXT,
    user_agent_hash TEXT,
    session_metadata JSONB NOT NULL DEFAULT '{}',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    UNIQUE(username, channel)
);

CREATE TABLE IF NOT EXISTS behavior_profiles (
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    message_count INT NOT NULL DEFAULT 0,
    avg_msg_length FLOAT NOT NULL DEFAULT 0,
    avg_typing_speed FLOAT NOT NULL DEFAULT 0,
    caps_ratio FLOAT NOT NULL DEFAULT 0,
    emoji_frequency FLOAT NOT NULL DEFAULT 0,
    emoji_profile JSONB NOT NULL DEFAULT '{}',
    vocab_fingerprint JSONB NOT NULL DEFAULT '{}',
    timing_histogram JSONB NOT NULL DEFAULT '{}',
    msg_length_stats JSONB NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (username, channel)
);

CREATE TABLE IF NOT EXISTS user_challenges (
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    challenge_type TEXT NOT NULL,
    challenge_status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    expires_at TEXT,
    completed_at TEXT,
    PRIMARY KEY (username, channel)
);

CREATE TABLE IF NOT EXISTS whitelisted_users (
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    added_by TEXT,
    reason TEXT,
    tier TEXT NOT NULL DEFAULT 'regular',
    auto_whitelisted BOOLEAN NOT NULL DEFAULT FALSE,
    message_count_at_whitelist INT NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (username, channel)
);

CREATE TABLE IF NOT EXISTS moderation_actions (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    action TEXT NOT NULL,
    risk_score_at_action FLOAT,
    features JSONB NOT NULL DEFAULT '{}',
    performed_by TEXT NOT NULL DEFAULT 'system',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_model_weights (
    channel TEXT PRIMARY KEY,
    feature_weights JSONB NOT NULL DEFAULT '{}',
    training_samples INT NOT NULL DEFAULT 0,
    last_trained_at TEXT,
    model_version INT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS raid_events (
    id SERIAL PRIMARY KEY,
    channel TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    severity TEXT NOT NULL,
    new_chatters_count INT NOT NULL,
    window_seconds INT NOT NULL,
    suspicious_accounts JSONB NOT NULL DEFAULT '[]',
    auto_action_taken TEXT NOT NULL DEFAULT 'none',
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS raid_settings (
    id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    new_chatter_threshold INT NOT NULL DEFAULT 20,
    window_seconds INT NOT NULL DEFAULT 60,
    auto_action TEXT NOT NULL DEFAULT 'none',
    min_account_age_days INT NOT NULL DEFAULT 7
);

CREATE TABLE IF NOT EXISTS giveaway_fraud_flags (
    id SERIAL PRIMARY KEY,
    giveaway_id TEXT NOT NULL,
    username TEXT NOT NULL,
    flag_type TEXT NOT NULL,
    matched_username TEXT,
    confidence FLOAT NOT NULL,
    reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    review_action TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tournaments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    channel TEXT NOT NULL,
    game TEXT NOT NULL DEFAULT '',
    max_participants INT NOT NULL DEFAULT 16,
    format TEXT NOT NULL DEFAULT 'single_elimination',
    keyword TEXT NOT NULL DEFAULT '!join',
    status TEXT NOT NULL DEFAULT 'registration',
    participants JSONB NOT NULL DEFAULT '[]',
    matches JSONB NOT NULL DEFAULT '[]',
    current_round INT NOT NULL DEFAULT 0,
    winner TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS saved_ideas (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    estimated_cost TEXT NOT NULL DEFAULT 'Free',
    engagement_level TEXT NOT NULL DEFAULT 'medium',
    requirements JSONB NOT NULL DEFAULT '[]',
    saved BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    access_token TEXT,
    refresh_token TEXT,
    expires_in INT,
    token_type TEXT,
    scope TEXT,
    user_data JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS pending_auth (
    state TEXT PRIMARY KEY,
    code_verifier TEXT NOT NULL,
    session_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free',
    status TEXT NOT NULL DEFAULT 'active',
    lemon_subscription_id TEXT,
    lemon_customer_id TEXT,
    lemon_order_id TEXT,
    current_period_start TEXT,
    current_period_end TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS coach_settings (
    channel TEXT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    engagement_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    game_duration_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    viewer_change_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    raid_welcome_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    sentiment_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    break_reminders BOOLEAN NOT NULL DEFAULT TRUE,
    break_reminder_minutes INT NOT NULL DEFAULT 120,
    engagement_drop_threshold FLOAT NOT NULL DEFAULT 30.0,
    viewer_change_threshold INT NOT NULL DEFAULT 10
);

CREATE TABLE IF NOT EXISTS stream_sessions (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    started_at TEXT NOT NULL,
    ended_at TEXT,
    peak_viewers INT NOT NULL DEFAULT 0,
    avg_viewers FLOAT NOT NULL DEFAULT 0.0,
    total_messages INT NOT NULL DEFAULT 0,
    game TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS coach_suggestions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    type TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'info',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    dismissed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TEXT NOT NULL,
    dismissed_at TEXT
);

CREATE TABLE IF NOT EXISTS stream_snapshots (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    viewer_count INT NOT NULL DEFAULT 0,
    message_count INT NOT NULL DEFAULT 0,
    game TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL
);
"""


async def create_tables():
    """Create all tables if they don't exist."""
    async with get_conn() as conn:
        await conn.execute(SCHEMA_SQL)
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
            """INSERT INTO bot_configs (channel, prefix, enabled, welcome_message, auto_mod_enabled)
               VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            (channel, "!", True, "Welcome to the stream, {username}! Type !commands to see what I can do.", True),
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

        await conn.commit()
