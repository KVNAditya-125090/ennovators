"""
Cloud SQL (PostgreSQL) - MaaS (Management as a Service)
Relational, multi-tenant system of record: tenants, users and RBAC roles.
"""

from typing import Dict, Any, List, Optional
import hashlib
import hmac

TENANTS = [
    {"tenant_id": "5a9948a4-8637-5418-bb7d-544d070d9ac6", "name": "GreenCycle Refurbishers", "type": "Certified Refurbisher", "status": "Active", "users_count": 18}
]

USERS = [
    {"user_id": "a92e3fbf-419f-5693-a479-1415c4d7271f", "name": "AIONOS", "email": "admin@auracommerce.io", "role": "Owner / Manager", "tenant": "Aura Eco Retail"},
    {"user_id": "755606bc-31a4-5ada-b5dd-50741a50b150", "name": "Sarah Chen", "email": "seller@greencycle.com", "role": "Consumer / Root", "tenant": "GreenCycle Refurbishers"},
    {"user_id": "5635f3c2-a835-58af-b4e8-8aa5444b0604", "name": "Marcus Vance", "email": "customer@gmail.com", "role": "Customer / Individual", "tenant": "Direct Shopper"},
    {"user_id": "f349ae73-034e-5c4d-9d57-d141fde4c45a", "name": "Rahul Mehta", "email": "rahul@greencycle.com", "role": "Consumer / Manager", "tenant": "GreenCycle Refurbishers"},
    {"user_id": "3501c2d0-3d4c-5b0d-b776-56dd2a068882", "name": "Priya Nair", "email": "priya@greencycle.com", "role": "Consumer / Dispatcher", "tenant": "GreenCycle Refurbishers"},
    {"user_id": "d116c066-e773-5a93-9b7f-f5e434bf2747", "name": "Anika Rao", "email": "anika@greencycle.com", "role": "Consumer / Seller", "tenant": "GreenCycle Refurbishers"},
    {"user_id": "908db58d-66ba-5c26-bad9-1081f3c5cf52", "name": "Neha Iyer", "email": "developer@auracommerce.io", "role": "Owner / Developer", "tenant": "Aura Eco Retail"},
    {"user_id": "0ce37583-16e9-52cf-8631-5c9d578f3ebf", "name": "Karan Patel", "email": "operator@auracommerce.io", "role": "Owner / Operator", "tenant": "Aura Eco Retail"}
]

# Each consumer's own profile data. All values are made-up samples; addresses use the reserved .example domain.
TENANT_PROFILES = {
    "5a9948a4-8637-5418-bb7d-544d070d9ac6": {
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
    "admin@auracommerce.io": {"password_hash": _hash("Owner@123"), "user_id": "a92e3fbf-419f-5693-a479-1415c4d7271f", "portal": "Owner"},
    "seller@greencycle.com": {"password_hash": _hash("Seller@123"), "user_id": "755606bc-31a4-5ada-b5dd-50741a50b150", "portal": "Consumer"},
    "customer@gmail.com": {"password_hash": _hash("Customer@123"), "user_id": "5635f3c2-a835-58af-b4e8-8aa5444b0604", "portal": "Customer"},
    # The other Owner roles. For now each sees everything the Owner Manager sees; the per-role limits come later.
    "developer@auracommerce.io": {"password_hash": _hash("Developer@123"), "user_id": "908db58d-66ba-5c26-bad9-1081f3c5cf52", "portal": "Owner"},
    "operator@auracommerce.io": {"password_hash": _hash("Operator@123"), "user_id": "0ce37583-16e9-52cf-8631-5c9d578f3ebf", "portal": "Owner"},
    # The other Consumer roles of GreenCycle (seller@greencycle.com above is its Root)
    "rahul@greencycle.com": {"password_hash": _hash("Manager@123"), "user_id": "f349ae73-034e-5c4d-9d57-d141fde4c45a", "portal": "Consumer"},
    "anika@greencycle.com": {"password_hash": _hash("Seller@123"), "user_id": "d116c066-e773-5a93-9b7f-f5e434bf2747", "portal": "Consumer"},
    "priya@greencycle.com": {"password_hash": _hash("Dispatcher@123"), "user_id": "3501c2d0-3d4c-5b0d-b776-56dd2a068882", "portal": "Consumer"},
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
