"""
Cloud Run - who is calling, and what they may call.
Every call must name the person making it (the X-User-Email header, or ?email= on the endpoints list).
The Root may call every endpoint the workspace opted into. Everyone else may call only what the roles they hold allow
(set on the Roles and Team page), and sees only the pages the Root chose for their role on the Customization page.
An unnamed caller, or someone who does not belong to the workspace, gets nothing (fails closed).
Preview limit: there is no token yet, so the email is trusted as sent; a real sign-in must replace this.
"""

from typing import Any, Dict, List, Optional, Set

from cloud_sql.services.maas import cloud_sql_maas
from firestore.users.consumer import operations as ops

def find_user(email: Optional[str]) -> Optional[Dict[str, Any]]:
    if not email:
        return None
    email = email.strip().lower()
    return next((u for u in cloud_sql_maas.list_users() if u["email"].lower() == email), None)

def is_owner(email: Optional[str]) -> bool:
    user = find_user(email)
    return bool(user and user["role"].startswith("Owner"))

def _member(user: Optional[Dict[str, Any]], tenant_name: Optional[str]) -> bool:
    return bool(user and user["role"].startswith("Consumer") and (tenant_name is None or user["tenant"] == tenant_name))

def _held_roles(email: str) -> List[str]:
    active = {r["role_id"] for r in ops.ROLES if r["active"]}
    return [m["role_id"] for m in ops.ROLE_MAILS if m["mail"] == email.strip().lower() and m["role_id"] in active]

def allowed_paths(email: Optional[str], tenant_name: Optional[str] = None) -> Optional[Set[str]]:
    """The endpoint paths this person may call: None means no limit (the Root), an empty set means nothing."""
    user = find_user(email)
    if not _member(user, tenant_name):
        return set()
    if user["role"].endswith("Root"):
        return None
    return set().union(*(ops.ROLE_PERMISSIONS.get(role_id, set()) for role_id in _held_roles(email)))

def role_view(email: Optional[str], tenant_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """The pages the Root chose for this person's role(s), merged. None means no narrowing (the Root, or no view set)."""
    user = find_user(email)
    if not _member(user, tenant_name) or user["role"].endswith("Root"):
        return None
    views = (ops.TEMPLATE or {}).get("role_views", {})
    chosen = [views[r] for r in _held_roles(email) if r in views]
    if not chosen:
        return None
    pages = list(dict.fromkeys(p for v in chosen for p in v.get("pages", [])))
    landing = next((v["landing"] for v in chosen if v.get("landing") in pages), pages[0] if pages else None)
    return {"landing": landing, "pages": pages}

# ---- What a consumer's customers see: opt-in, then the published storefront template ----

def published_template() -> Optional[Dict[str, Any]]:
    """The storefront the consumer published for its customers, or None when nothing is published yet."""
    t = ops.TEMPLATE
    return t if t and t.get("published") else None

def customer_sections() -> Optional[Set[str]]:
    """The features the consumer chose to show customers on the published template. None means no narrowing
    (nothing published, or no feature picked, so every opted-in feature shows)."""
    t = published_template()
    chosen = {s if isinstance(s, str) else s.get("path") for s in (t or {}).get("sections", [])}
    return chosen or None

def customer_may_use(tenant_id: str, path: str) -> bool:
    """True when the Owner opted the consumer into this endpoint and the consumer's published template shows it."""
    from cloud_sql.services.maas.endpoints import endpoint_registry
    if path not in endpoint_registry.enabled_paths(tenant_id):
        return False
    shown = customer_sections()
    return shown is None or path in shown

def customer_brand(consumer_name: str) -> Dict[str, Any]:
    """The consumer's published look for its storefront (what customers see instead of the platform's own)."""
    t = published_template()
    if not t:
        return {"published": False}
    return {"published": True, "version": t.get("version"), "name": t.get("name"),
            "layout": t.get("layout", {}), "branding": {**t.get("branding", {}), "brand_name": t.get("branding", {}).get("brand_name") or consumer_name}}
