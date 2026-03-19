"""White-Label Platform (B2B) router."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth
from app.models.schemas import (
    OrganizationCreate, OrganizationUpdate,
    OrgMemberAdd, OrgBrandingUpdate, OrgSettingsUpdate,
)
from app.repositories import whitelabel as wl_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whitelabel", tags=["whitelabel"])


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

@router.post("/orgs")
async def create_org(
    body: OrganizationCreate, session: dict = Depends(require_auth)
) -> dict:
    # Check if slug is taken
    existing = await wl_repo.get_org_by_slug(body.slug)
    if existing:
        raise HTTPException(status_code=409, detail="Organization slug already taken")
    owner_id = session.get("user_id", session.get("session_id", ""))
    return await wl_repo.create_org(
        name=body.name, slug=body.slug, owner_user_id=owner_id,
        plan=body.plan, max_members=body.max_members, custom_domain=body.custom_domain,
    )


@router.get("/orgs")
async def list_user_orgs(session: dict = Depends(require_auth)) -> list[dict]:
    user_id = session.get("user_id", session.get("session_id", ""))
    return await wl_repo.get_user_orgs(user_id)


@router.get("/orgs/{org_id}")
async def get_org(org_id: str, _session: dict = Depends(require_auth)) -> dict:
    org = await wl_repo.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.put("/orgs/{org_id}")
async def update_org(
    org_id: str, body: OrganizationUpdate, _session: dict = Depends(require_auth)
) -> dict:
    org = await wl_repo.update_org(
        org_id,
        name=body.name,
        plan=body.plan,
        max_members=body.max_members,
        custom_domain=body.custom_domain,
        status=body.status,
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.delete("/orgs/{org_id}")
async def delete_org(org_id: str, _session: dict = Depends(require_auth)) -> dict:
    deleted = await wl_repo.delete_org(org_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------

@router.post("/orgs/{org_id}/members")
async def add_member(
    org_id: str, body: OrgMemberAdd, _session: dict = Depends(require_auth)
) -> dict:
    org = await wl_repo.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    # Check member limit
    members = await wl_repo.get_members(org_id)
    if len(members) >= org.get("max_members", 5):
        raise HTTPException(status_code=400, detail="Member limit reached. Upgrade your plan.")
    return await wl_repo.add_member(
        org_id=org_id, user_id=body.user_id, username=body.username,
        role=body.role, channel=body.channel,
    )


@router.get("/orgs/{org_id}/members")
async def list_members(
    org_id: str, _session: dict = Depends(require_auth)
) -> list[dict]:
    return await wl_repo.get_members(org_id)


@router.delete("/orgs/{org_id}/members/{user_id}")
async def remove_member(
    org_id: str, user_id: str, _session: dict = Depends(require_auth)
) -> dict:
    org = await wl_repo.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if user_id == org.get("owner_user_id"):
        raise HTTPException(status_code=400, detail="Cannot remove the organization owner")
    removed = await wl_repo.remove_member(org_id, user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"removed": True}


# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------

@router.get("/orgs/{org_id}/branding")
async def get_branding(
    org_id: str, _session: dict = Depends(require_auth)
) -> dict:
    return await wl_repo.get_branding(org_id)


@router.put("/orgs/{org_id}/branding")
async def update_branding(
    org_id: str, body: OrgBrandingUpdate, _session: dict = Depends(require_auth)
) -> dict:
    return await wl_repo.update_branding(
        org_id=org_id,
        logo_url=body.logo_url,
        primary_color=body.primary_color,
        secondary_color=body.secondary_color,
        accent_color=body.accent_color,
        dark_mode=body.dark_mode,
        custom_css=body.custom_css,
        welcome_message=body.welcome_message,
    )


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@router.get("/orgs/{org_id}/settings")
async def get_settings(
    org_id: str, _session: dict = Depends(require_auth)
) -> dict:
    return await wl_repo.get_settings(org_id)


@router.put("/orgs/{org_id}/settings")
async def update_settings(
    org_id: str, body: OrgSettingsUpdate, _session: dict = Depends(require_auth)
) -> dict:
    return await wl_repo.update_settings(
        org_id=org_id,
        features_enabled=body.features_enabled,
        default_role=body.default_role,
        require_approval=body.require_approval,
        billing_email=body.billing_email,
    )


# ---------------------------------------------------------------------------
# Aggregate Analytics
# ---------------------------------------------------------------------------

@router.get("/orgs/{org_id}/analytics")
async def get_org_analytics(
    org_id: str, _session: dict = Depends(require_auth)
) -> dict:
    """Aggregate analytics for all streamers in the org."""
    org = await wl_repo.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    members = await wl_repo.get_members(org_id)
    return {
        "org_id": org_id,
        "org_name": org["name"],
        "total_members": len(members),
        "members": [
            {"user_id": m["user_id"], "username": m["username"],
             "role": m["role"], "channel": m.get("channel")}
            for m in members
        ],
        "plan": org.get("plan", "starter"),
    }
