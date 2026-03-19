"""White-label platform schemas."""

from pydantic import BaseModel
from typing import Optional


class OrganizationCreate(BaseModel):
    name: str
    slug: str
    plan: str = "starter"
    max_members: int = 5
    custom_domain: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None
    max_members: Optional[int] = None
    custom_domain: Optional[str] = None
    status: Optional[str] = None


class Organization(BaseModel):
    id: Optional[str] = None
    name: str
    slug: str
    owner_user_id: str
    plan: str = "starter"
    status: str = "active"
    max_members: int = 5
    custom_domain: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class OrgMemberAdd(BaseModel):
    user_id: str
    username: str
    role: str = "viewer"  # "admin", "manager", "viewer"
    channel: Optional[str] = None


class OrgMember(BaseModel):
    id: Optional[str] = None
    org_id: str
    user_id: str
    username: str
    role: str = "viewer"
    channel: Optional[str] = None
    joined_at: Optional[str] = None


class OrgBrandingUpdate(BaseModel):
    logo_url: Optional[str] = None
    primary_color: str = "#10b981"
    secondary_color: str = "#6366f1"
    accent_color: str = "#f59e0b"
    dark_mode: bool = True
    custom_css: Optional[str] = None
    welcome_message: Optional[str] = None


class OrgBranding(BaseModel):
    org_id: str
    logo_url: Optional[str] = None
    primary_color: str = "#10b981"
    secondary_color: str = "#6366f1"
    accent_color: str = "#f59e0b"
    dark_mode: bool = True
    custom_css: Optional[str] = None
    welcome_message: Optional[str] = None
    updated_at: Optional[str] = None


class OrgSettingsUpdate(BaseModel):
    features_enabled: list[str] = ["coach", "analytics", "clips", "heatmap"]
    default_role: str = "viewer"
    require_approval: bool = False
    billing_email: Optional[str] = None
