"""Domain-specific database schema modules.

Each module exports a SCHEMA_SQL string containing CREATE TABLE statements
for its domain. The `all_schemas()` helper returns them concatenated in
dependency order so that `create_tables()` can execute a single string.
"""

from app.services.schema.auth import SCHEMA_SQL as AUTH_SCHEMA
from app.services.schema.bot import SCHEMA_SQL as BOT_SCHEMA
from app.services.schema.chat import SCHEMA_SQL as CHAT_SCHEMA
from app.services.schema.giveaway import SCHEMA_SQL as GIVEAWAY_SCHEMA
from app.services.schema.antialt import SCHEMA_SQL as ANTIALT_SCHEMA
from app.services.schema.tournament import SCHEMA_SQL as TOURNAMENT_SCHEMA
from app.services.schema.subscription import SCHEMA_SQL as SUBSCRIPTION_SCHEMA
from app.services.schema.analytics import SCHEMA_SQL as ANALYTICS_SCHEMA
from app.services.schema.coach import SCHEMA_SQL as COACH_SCHEMA
from app.services.schema.clips import SCHEMA_SQL as CLIPS_SCHEMA
from app.services.schema.heatmap import SCHEMA_SQL as HEATMAP_SCHEMA
from app.services.schema.whitelabel import SCHEMA_SQL as WHITELABEL_SCHEMA
from app.services.schema.marketplace import SCHEMA_SQL as MARKETPLACE_SCHEMA
from app.services.schema.loyalty import SCHEMA_SQL as LOYALTY_SCHEMA
from app.services.schema.songs import SCHEMA_SQL as SONGS_SCHEMA
from app.services.schema.schedule import SCHEMA_SQL as SCHEDULE_SCHEMA
from app.services.schema.profiles import SCHEMA_SQL as PROFILES_SCHEMA
from app.services.schema.overlays import SCHEMA_SQL as OVERLAYS_SCHEMA
from app.services.schema.intelligence import SCHEMA_SQL as INTELLIGENCE_SCHEMA
from app.services.schema.viewer_crm import SCHEMA_SQL as VIEWER_CRM_SCHEMA
from app.services.schema.debrief import SCHEMA_SQL as DEBRIEF_SCHEMA
from app.services.schema.discord import SCHEMA_SQL as DISCORD_SCHEMA
from app.services.schema.revenue import SCHEMA_SQL as REVENUE_SCHEMA
from app.services.schema.highlights import SCHEMA_SQL as HIGHLIGHTS_SCHEMA
from app.services.schema.engagement import SCHEMA_SQL as ENGAGEMENT_SCHEMA
from app.services.schema.translation import SCHEMA_SQL as TRANSLATION_SCHEMA
from app.services.schema.activity import SCHEMA_SQL as ACTIVITY_SCHEMA

_ALL_SCHEMAS = [
    AUTH_SCHEMA,
    BOT_SCHEMA,
    CHAT_SCHEMA,
    GIVEAWAY_SCHEMA,
    ANTIALT_SCHEMA,
    TOURNAMENT_SCHEMA,
    SUBSCRIPTION_SCHEMA,
    ANALYTICS_SCHEMA,
    COACH_SCHEMA,
    CLIPS_SCHEMA,
    HEATMAP_SCHEMA,
    WHITELABEL_SCHEMA,
    MARKETPLACE_SCHEMA,
    LOYALTY_SCHEMA,
    SONGS_SCHEMA,
    SCHEDULE_SCHEMA,
    PROFILES_SCHEMA,
    OVERLAYS_SCHEMA,
    INTELLIGENCE_SCHEMA,
    VIEWER_CRM_SCHEMA,
    DEBRIEF_SCHEMA,
    DISCORD_SCHEMA,
    REVENUE_SCHEMA,
    HIGHLIGHTS_SCHEMA,
    ENGAGEMENT_SCHEMA,
    TRANSLATION_SCHEMA,
    ACTIVITY_SCHEMA,
]


def all_schemas() -> str:
    """Return all schema SQL concatenated in dependency order."""
    return "\n".join(_ALL_SCHEMAS)
