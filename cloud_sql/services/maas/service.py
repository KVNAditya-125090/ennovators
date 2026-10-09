"""
Cloud SQL (PostgreSQL) - MaaS (Management as a Service)
Relational, multi-tenant system of record: tenants, users and RBAC roles.
"""

from typing import Dict, Any, List, Optional
import hashlib
import hmac

TENANTS = [
    {"tenant_id": "t-001", "name": "GreenCycle Refurbishers", "type": "Certified Refurbisher", "status": "Active", "users_count": 18}
]

USERS = [
    {"user_id": "usr-101", "name": "AIONOS", "email": "admin@auracommerce.io", "role": "Owner / Manager", "tenant": "Aura Eco Retail"},
    {"user_id": "usr-102", "name": "Sarah Chen", "email": "seller@greencycle.com", "role": "Consumer / Root", "tenant": "GreenCycle Refurbishers"},
    {"user_id": "usr-103", "name": "Marcus Vance", "email": "customer@gmail.com", "role": "Customer / Individual", "tenant": "Direct Shopper"},
    {"user_id": "usr-104", "name": "Rahul Mehta", "email": "rahul@greencycle.com", "role": "Consumer / Manager", "tenant": "GreenCycle Refurbishers"},
    {"user_id": "usr-105", "name": "Priya Nair", "email": "priya@greencycle.com", "role": "Consumer / Dispatcher", "tenant": "GreenCycle Refurbishers"},
    {"user_id": "usr-106", "name": "Anika Rao", "email": "anika@greencycle.com", "role": "Consumer / Seller", "tenant": "GreenCycle Refurbishers"},
    {"user_id": "usr-107", "name": "Neha Iyer", "email": "developer@auracommerce.io", "role": "Owner / Developer", "tenant": "Aura Eco Retail"},
    {"user_id": "usr-108", "name": "Karan Patel", "email": "operator@auracommerce.io", "role": "Owner / Operator", "tenant": "Aura Eco Retail"}
]

# Each consumer's own profile data. All values are made-up samples; addresses use the reserved .example domain.
TENANT_PROFILES = {
    "t-001": {
        "company": {"legal_name": "GreenCycle Refurbishers LLP", "industry": "Refurbishment and repair", "location": "Pune, India", "address": "27 Baner Road, Pune, Maharashtra 411045, India", "website": "greencycle.example", "joined": "2026-02-18"},
        "billing": {"plan": "Growth", "billing_cycle": "Monthly", "payment_status": "Paid", "next_invoice": "2026-11-01"},
        "contact": {"name": "Sarah Chen", "title": "Operations Lead", "email": "sarah.chen@greencycle.example", "phone": "+91 20 5550 0102", "department": "Operations", "alt_phone": "+91 20 5550 0112", "preferred_contact": "Phone", "timezone": "IST (UTC+5:30)", "working_hours": "Mon-Sat, 10:00-19:00"},
    },
}

def _hash(password: str) -> str:
    return hashlib.sha256(("auracommerce-demo:" + password).encode("utf-8")).hexdigest()

# Demo accounts for preview mode. The account decides the portal; replace with real
# sign-in (for example Firebase Authentication) before any production use.
ACCOUNTS = {
    "admin@auracommerce.io": {"password_hash": _hash("Owner@123"), "user_id": "usr-101", "portal": "Owner"},
    "seller@greencycle.com": {"password_hash": _hash("Seller@123"), "user_id": "usr-102", "portal": "Consumer"},
    "customer@gmail.com": {"password_hash": _hash("Customer@123"), "user_id": "usr-103", "portal": "Customer"},
    # The other Owner roles. For now each sees everything the Owner Manager sees; the per-role limits come later.
    "developer@auracommerce.io": {"password_hash": _hash("Developer@123"), "user_id": "usr-107", "portal": "Owner"},
    "operator@auracommerce.io": {"password_hash": _hash("Operator@123"), "user_id": "usr-108", "portal": "Owner"},
    # The other Consumer roles of GreenCycle (seller@greencycle.com above is its Root)
    "rahul@greencycle.com": {"password_hash": _hash("Manager@123"), "user_id": "usr-104", "portal": "Consumer"},
    "anika@greencycle.com": {"password_hash": _hash("Seller@123"), "user_id": "usr-106", "portal": "Consumer"},
    "priya@greencycle.com": {"password_hash": _hash("Dispatcher@123"), "user_id": "usr-105", "portal": "Consumer"},
}

class CloudSQLMaaS:
    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def list_tenants(self) -> List[Dict[str, Any]]:
        return TENANTS

    def list_users(self) -> List[Dict[str, Any]]:
        return USERS

    def get_profile(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        profile = TENANT_PROFILES.get(tenant_id)
        return None if profile is None else {group: dict(values) for group, values in profile.items()}

    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        return next((t for t in TENANTS if t["tenant_id"] == tenant_id), None)

    def get_tenant_by_name(self, tenant_name: str) -> Optional[Dict[str, Any]]:
        return next((t for t in TENANTS if t["name"] == tenant_name), None)

    def list_members(self, tenant_name: str) -> List[Dict[str, Any]]:
        return [u for u in USERS if u["tenant"] == tenant_name]

    def get_workspace(self, tenant_name: str) -> Optional[Dict[str, Any]]:
        """A tenant workspace with its team, for the consumers who run it."""
        tenant = next((t for t in TENANTS if t["name"] == tenant_name), None)
        if tenant is None:
            return None
        return {"tenant": tenant, "members": [u for u in USERS if u["tenant"] == tenant_name]}

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Returns the signed-in user, with the portal their account belongs to, or None."""
        account = ACCOUNTS.get(email.strip().lower())
        supplied = _hash(password)
        # compare even for unknown emails so response time does not reveal which emails exist
        expected = account["password_hash"] if account else _hash("")
        if not hmac.compare_digest(supplied, expected) or account is None:
            return None
        user = next(u for u in USERS if u["user_id"] == account["user_id"])
        return {"user_id": user["user_id"], "name": user["name"], "email": user["email"],
                "role": account["portal"], "tenant": user["tenant"],
                # sub-role shown beside the portal: Owner (Manager / Developer / Operator), Consumer (as registered)
                "department": user["role"].partition(" / ")[2] or None}

cloud_sql_maas = CloudSQLMaaS()
