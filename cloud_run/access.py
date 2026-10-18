"""
Cloud Run - who is calling, and what they may call.
Every call must name the person making it (the X-User-Email header, or ?email= on the endpoints list).
The Root may call every endpoint the workspace opted into. Everyone else may call only what the roles they hold allow
(set on the Roles and Team page), and sees only the pages the Root chose for their role on the Customization page.
An unnamed caller, or someone who does not belong to the workspace, gets nothing (fails closed).
The email comes from the verified sign-in token (cloud_run/auth.py), never from what the caller sends.
"""

import os
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException

from cloud_sql.services.maas import cloud_sql_maas
from cloud_sql.services.maas.roles import roles as role_store

def find_user(email: Optional[str]) -> Optional[Dict[str, Any]]:
    if not email:
        return None
    email = email.strip().lower()
    return cloud_sql_maas.find_user(email)

def default_tenant_id() -> Optional[str]:
    """The one consumer whose public storefront is shown (the DEFAULT_CONSUMER setting), or None."""
    name = os.environ.get("DEFAULT_CONSUMER", "")
    tenant = cloud_sql_maas.get_tenant_by_name(name) if name else None
    return tenant["tenant_id"] if tenant else None

def staff_tenant_id(email: Optional[str], tenant_name: Optional[str] = None) -> str:
    """The consumer a signed-in staff member works for. Raises 401 when nobody is signed in and 403 for anyone else."""
    user = find_user(email)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to use this.")
    if not user["role"].startswith("Consumer") or (tenant_name and user["tenant"] != tenant_name):
        raise HTTPException(status_code=403, detail="This workspace is not yours.")
    return user["tenant_id"]

def is_owner(email: Optional[str]) -> bool:
    user = find_user(email)
    return bool(user and user["role"].startswith("Owner"))

def _member(user: Optional[Dict[str, Any]], tenant_name: Optional[str]) -> bool:
    return bool(user and user["role"].startswith("Consumer") and (tenant_name is None or user["tenant"] == tenant_name))

def allowed_paths(email: Optional[str], tenant_name: Optional[str] = None) -> Optional[Set[str]]:
    """The endpoint paths this person may call: None means no limit (the Root), an empty set means nothing."""
    user = find_user(email)
    if not _member(user, tenant_name):
        return set()
    if user["role"].endswith("Root"):
        return None
    return role_store.allowed_paths(user["tenant_id"], user["email"])

def role_view(email: Optional[str], tenant_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """The pages the Root chose for this person's role(s), merged. None means no narrowing (the Root, or no view set)."""
    user = find_user(email)
    if not _member(user, tenant_name) or user["role"].endswith("Root"):
        return None
    views = role_store.get_template(user["tenant_id"]).get("role_views", {})
    chosen = [views[r] for r in role_store.held_roles(user["tenant_id"], user["email"]) if r in views]
    if not chosen:
        return None
    pages = list(dict.fromkeys(p for v in chosen for p in v.get("pages", [])))
    landing = next((v["landing"] for v in chosen if v.get("landing") in pages), pages[0] if pages else None)
    return {"landing": landing, "pages": pages}

# ---- What a consumer's customers see: opt-in, then the published storefront template ----

def published_template(tenant_id: str) -> Optional[Dict[str, Any]]:
    """The storefront the consumer published for its customers, or None when nothing is published yet."""
    t = role_store.get_template(tenant_id)
    return t if t and t.get("published") else None

def customer_sections(tenant_id: str) -> Optional[Set[str]]:
    """The features the consumer chose to show customers on the published template. None means no narrowing
    (nothing published, or no feature picked, so every opted-in feature shows)."""
    t = published_template(tenant_id)
    chosen = {s if isinstance(s, str) else s.get("path") for s in (t or {}).get("sections", [])}
    return chosen or None

def customer_may_use(tenant_id: str, path: str) -> bool:
    """True when the Owner opted the consumer into this endpoint and the consumer's published template shows it."""
    from cloud_sql.services.maas.endpoints import endpoint_registry
    if path not in endpoint_registry.enabled_paths(tenant_id):
        return False
    shown = customer_sections(tenant_id)
    return shown is None or path in shown

def customer_brand(tenant_id: str, consumer_name: str) -> Dict[str, Any]:
    """The consumer's published look for its storefront (what customers see instead of the platform's own)."""
    t = published_template(tenant_id)
    if not t:
        return {"published": False}
    return {"published": True, "version": t.get("version"), "name": t.get("name"),
            "layout": t.get("layout", {}), "branding": {**t.get("branding", {}), "brand_name": t.get("branding", {}).get("brand_name") or consumer_name}}
