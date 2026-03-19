"""Repository for White-Label Platform data access."""

import json

from app.services.db import get_conn, _generate_id, _now_iso


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

async def create_org(
    name: str, slug: str, owner_user_id: str, plan: str, max_members: int,
    custom_domain: str | None,
) -> dict:
    org_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO organizations
               (id, name, slug, owner_user_id, plan, status, max_members, custom_domain, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,'active',%s,%s,%s,%s)""",
            (org_id, name, slug, owner_user_id, plan, max_members, custom_domain, now, now),
        )
        # Create default branding
        await conn.execute(
            """INSERT INTO org_branding (org_id, updated_at)
               VALUES (%s, %s) ON CONFLICT DO NOTHING""",
            (org_id, now),
        )
        # Create default settings
        await conn.execute(
            """INSERT INTO org_settings (org_id, updated_at)
               VALUES (%s, %s) ON CONFLICT DO NOTHING""",
            (org_id, now),
        )
        # Add owner as admin member
        member_id = _generate_id()
        await conn.execute(
            """INSERT INTO org_members (id, org_id, user_id, username, role, joined_at)
               VALUES (%s,%s,%s,%s,'admin',%s)""",
            (member_id, org_id, owner_user_id, name, now),
        )
        await conn.commit()
    return {
        "id": org_id, "name": name, "slug": slug, "owner_user_id": owner_user_id,
        "plan": plan, "status": "active", "max_members": max_members,
        "custom_domain": custom_domain, "created_at": now, "updated_at": now,
    }


async def get_org(org_id: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM organizations WHERE id = %s", (org_id,)
        )
        row = await cur.fetchone()
    return dict(row) if row else None


async def get_org_by_slug(slug: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM organizations WHERE slug = %s", (slug,)
        )
        row = await cur.fetchone()
    return dict(row) if row else None


async def get_user_orgs(user_id: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT o.* FROM organizations o
               JOIN org_members m ON o.id = m.org_id
               WHERE m.user_id = %s ORDER BY o.created_at DESC""",
            (user_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def update_org(org_id: str, **kwargs: object) -> dict | None:
    now = _now_iso()
    allowed = {"name", "plan", "max_members", "custom_domain", "status"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return await get_org(org_id)

    set_parts = [f"{k} = %s" for k in updates]
    set_parts.append("updated_at = %s")
    values = list(updates.values())
    values.append(now)
    values.append(org_id)

    async with get_conn() as conn:
        await conn.execute(
            f"UPDATE organizations SET {', '.join(set_parts)} WHERE id = %s",
            tuple(values),
        )
        await conn.commit()
    return await get_org(org_id)


async def delete_org(org_id: str) -> bool:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM org_members WHERE org_id = %s", (org_id,))
        await conn.execute("DELETE FROM org_branding WHERE org_id = %s", (org_id,))
        await conn.execute("DELETE FROM org_settings WHERE org_id = %s", (org_id,))
        result = await conn.execute("DELETE FROM organizations WHERE id = %s", (org_id,))
        await conn.commit()
        return result.rowcount > 0


# ---------------------------------------------------------------------------
# Org Members
# ---------------------------------------------------------------------------

async def add_member(
    org_id: str, user_id: str, username: str, role: str, channel: str | None
) -> dict:
    member_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO org_members (id, org_id, user_id, username, role, channel, joined_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (org_id, user_id) DO UPDATE SET role = EXCLUDED.role, channel = EXCLUDED.channel""",
            (member_id, org_id, user_id, username, role, channel, now),
        )
        await conn.commit()
    return {
        "id": member_id, "org_id": org_id, "user_id": user_id,
        "username": username, "role": role, "channel": channel, "joined_at": now,
    }


async def get_members(org_id: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM org_members WHERE org_id = %s ORDER BY joined_at ASC",
            (org_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_member(org_id: str, user_id: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM org_members WHERE org_id = %s AND user_id = %s",
            (org_id, user_id),
        )
        row = await cur.fetchone()
    return dict(row) if row else None


async def remove_member(org_id: str, user_id: str) -> bool:
    async with get_conn() as conn:
        result = await conn.execute(
            "DELETE FROM org_members WHERE org_id = %s AND user_id = %s",
            (org_id, user_id),
        )
        await conn.commit()
        return result.rowcount > 0


async def update_member_role(org_id: str, user_id: str, role: str) -> bool:
    async with get_conn() as conn:
        result = await conn.execute(
            "UPDATE org_members SET role = %s WHERE org_id = %s AND user_id = %s",
            (role, org_id, user_id),
        )
        await conn.commit()
        return result.rowcount > 0


# ---------------------------------------------------------------------------
# Org Branding
# ---------------------------------------------------------------------------

async def get_branding(org_id: str) -> dict:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM org_branding WHERE org_id = %s", (org_id,)
        )
        row = await cur.fetchone()
    if row:
        return dict(row)
    return {
        "org_id": org_id, "logo_url": None, "primary_color": "#10b981",
        "secondary_color": "#6366f1", "accent_color": "#f59e0b",
        "dark_mode": True, "custom_css": None, "welcome_message": None,
    }


async def update_branding(
    org_id: str, logo_url: str | None, primary_color: str, secondary_color: str,
    accent_color: str, dark_mode: bool, custom_css: str | None, welcome_message: str | None,
) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO org_branding
               (org_id, logo_url, primary_color, secondary_color, accent_color,
                dark_mode, custom_css, welcome_message, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (org_id) DO UPDATE SET
                 logo_url = EXCLUDED.logo_url,
                 primary_color = EXCLUDED.primary_color,
                 secondary_color = EXCLUDED.secondary_color,
                 accent_color = EXCLUDED.accent_color,
                 dark_mode = EXCLUDED.dark_mode,
                 custom_css = EXCLUDED.custom_css,
                 welcome_message = EXCLUDED.welcome_message,
                 updated_at = EXCLUDED.updated_at""",
            (org_id, logo_url, primary_color, secondary_color, accent_color,
             dark_mode, custom_css, welcome_message, now),
        )
        await conn.commit()
    return await get_branding(org_id)


# ---------------------------------------------------------------------------
# Org Settings
# ---------------------------------------------------------------------------

async def get_settings(org_id: str) -> dict:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM org_settings WHERE org_id = %s", (org_id,)
        )
        row = await cur.fetchone()
    if row:
        d = dict(row)
        if isinstance(d.get("features_enabled"), str):
            d["features_enabled"] = json.loads(d["features_enabled"])
        return d
    return {
        "org_id": org_id, "features_enabled": ["coach", "analytics", "clips", "heatmap"],
        "default_role": "viewer", "require_approval": False, "billing_email": None,
    }


async def update_settings(
    org_id: str, features_enabled: list[str], default_role: str,
    require_approval: bool, billing_email: str | None,
) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO org_settings
               (org_id, features_enabled, default_role, require_approval, billing_email, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s)
               ON CONFLICT (org_id) DO UPDATE SET
                 features_enabled = EXCLUDED.features_enabled,
                 default_role = EXCLUDED.default_role,
                 require_approval = EXCLUDED.require_approval,
                 billing_email = EXCLUDED.billing_email,
                 updated_at = EXCLUDED.updated_at""",
            (org_id, json.dumps(features_enabled), default_role,
             require_approval, billing_email, now),
        )
        await conn.commit()
    return await get_settings(org_id)
