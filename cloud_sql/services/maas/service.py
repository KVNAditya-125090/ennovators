"""
Cloud SQL (PostgreSQL) - MaaS (Management as a Service)
Relational, multi-tenant system of record: tenants, users and RBAC roles.
"""

from typing import Dict, Any, List, Optional
import hashlib
import hmac

TENANTS = [
    {"tenant_id": "t-001", "name": "Aura Eco Retail", "type": "Primary Retailer", "status": "Active", "users_count": 42},
    {"tenant_id": "t-002", "name": "GreenCycle Refurbishers", "type": "Certified Refurbisher", "status": "Active", "users_count": 18},
    {"tenant_id": "t-003", "name": "NextLife Electronics", "type": "Third-Party Seller", "status": "Active", "users_count": 9}
]

USERS = [
    {"user_id": "usr-101", "name": "AIONOS", "email": "admin@auracommerce.io", "role": "Owner / SuperAdmin", "tenant": "Aura Eco Retail"},
    {"user_id": "usr-102", "name": "Sarah Chen", "email": "seller@greencycle.com", "role": "Consumer / Seller", "tenant": "GreenCycle Refurbishers"},
    {"user_id": "usr-103", "name": "Marcus Vance", "email": "customer@gmail.com", "role": "Customer", "tenant": "Direct Shopper"},
    {"user_id": "usr-104", "name": "Rahul Mehta", "email": "rahul@greencycle.com", "role": "Consumer / Manager", "tenant": "GreenCycle Refurbishers"},
    {"user_id": "usr-105", "name": "Priya Nair", "email": "priya@greencycle.com", "role": "Consumer / Dispatcher", "tenant": "GreenCycle Refurbishers"}
]

# Each consumer's own profile data. All values are made-up samples; addresses use the reserved .example domain.
TENANT_PROFILES = {
    "t-001": {
        "company": {"legal_name": "Aura Eco Retail Private Limited", "industry": "Retail", "location": "Bengaluru, India", "address": "14 Residency Road, Bengaluru, Karnataka 560025, India", "website": "auraecoretail.example", "joined": "2025-11-10"},
        "billing": {"plan": "Enterprise", "billing_cycle": "Monthly", "payment_status": "Paid", "next_invoice": "2026-11-01"},
        "contact": {"name": "Meera Iyer", "title": "Head of Operations", "email": "meera.iyer@auraecoretail.example", "phone": "+91 80 5550 0101", "department": "Operations", "alt_phone": "+91 80 5550 0111", "preferred_contact": "Email", "timezone": "IST (UTC+5:30)", "working_hours": "Mon-Fri, 9:00-18:00"},
    },
    "t-002": {
        "company": {"legal_name": "GreenCycle Refurbishers LLP", "industry": "Refurbishment and repair", "location": "Pune, India", "address": "27 Baner Road, Pune, Maharashtra 411045, India", "website": "greencycle.example", "joined": "2026-02-18"},
        "billing": {"plan": "Growth", "billing_cycle": "Monthly", "payment_status": "Paid", "next_invoice": "2026-11-01"},
        "contact": {"name": "Sarah Chen", "title": "Operations Lead", "email": "sarah.chen@greencycle.example", "phone": "+91 20 5550 0102", "department": "Operations", "alt_phone": "+91 20 5550 0112", "preferred_contact": "Phone", "timezone": "IST (UTC+5:30)", "working_hours": "Mon-Sat, 10:00-19:00"},
    },
    "t-003": {
        "company": {"legal_name": "NextLife Electronics Private Limited", "industry": "Consumer electronics", "location": "Hyderabad, India", "address": "8 Madhapur Main Road, Hyderabad, Telangana 500081, India", "website": "nextlife.example", "joined": "2026-06-22"},
        "billing": {"plan": "Starter", "billing_cycle": "Monthly", "payment_status": "Due", "next_invoice": "2026-10-15"},
        "contact": {"name": "Arjun Rao", "title": "Founder", "email": "arjun.rao@nextlife.example", "phone": "+91 40 5550 0103", "department": "Management", "alt_phone": "+91 40 5550 0113", "preferred_contact": "Email", "timezone": "IST (UTC+5:30)", "working_hours": "Mon-Fri, 9:30-18:30"},
    },
}

# Every API the platform offers, grouped by service. Consumers pay a monthly fee per enabled API
# plus a price per 1,000 requests.
API_CATALOG = [
    {"api_id": "workspace-management", "service": "MaaS", "name": "Workspace & Team Management", "description": "Workspace profile, team members and role-based access.", "monthly_fee_usd": 4.00, "price_per_1k_requests_usd": 0.10},
    {"api_id": "usage-analytics", "service": "MaaS", "name": "Analytics Dashboards", "description": "Sales, bid and circularity dashboards for the workspace.", "monthly_fee_usd": 6.00, "price_per_1k_requests_usd": 0.20},
    {"api_id": "product-catalog", "service": "PaaS", "name": "Product Catalog", "description": "List, update and search products and stock.", "monthly_fee_usd": 5.00, "price_per_1k_requests_usd": 0.40},
    {"api_id": "multi-seller-bidding", "service": "PaaS", "name": "Multi-Seller Bidding", "description": "Open bid rooms and collect seller offers.", "monthly_fee_usd": 8.00, "price_per_1k_requests_usd": 1.20},
    {"api_id": "demand-forecast", "service": "PaaS", "name": "Demand Forecasting (AI)", "description": "Per-product demand forecasts with reorder points.", "monthly_fee_usd": 12.00, "price_per_1k_requests_usd": 4.50},
    {"api_id": "shipment-tracking", "service": "TaaS", "name": "Shipment Tracking", "description": "Track forward and reverse shipments end to end.", "monthly_fee_usd": 5.00, "price_per_1k_requests_usd": 0.60},
    {"api_id": "reverse-logistics", "service": "TaaS", "name": "Reverse Logistics Routing", "description": "Route returned items to the best recovery channel.", "monthly_fee_usd": 6.00, "price_per_1k_requests_usd": 1.00},
    {"api_id": "ai-assistant", "service": "SaaS", "name": "AI Shopping Assistant", "description": "Voice and chat assistant for shopping and support.", "monthly_fee_usd": 10.00, "price_per_1k_requests_usd": 6.00},
    {"api_id": "return-grading", "service": "SaaS", "name": "Photo Return Grading (AI)", "description": "Condition grade and recovery value from return photos.", "monthly_fee_usd": 10.00, "price_per_1k_requests_usd": 8.00},
    {"api_id": "return-upload", "service": "SaaS", "name": "Return Photo Upload", "description": "Secure upload of return photos.", "monthly_fee_usd": 2.00, "price_per_1k_requests_usd": 0.30},
    {"api_id": "support-tickets", "service": "SaaS", "name": "Support Tickets", "description": "Open and track after-sales support tickets.", "monthly_fee_usd": 4.00, "price_per_1k_requests_usd": 0.50},
]
ALL_API_IDS = {api["api_id"] for api in API_CATALOG}

# Every API is addressed as /<service>/<feature>/<version>; this is the HTTP method each one uses
API_METHODS = {
    "workspace-management": "GET", "usage-analytics": "GET", "product-catalog": "GET", "multi-seller-bidding": "POST",
    "demand-forecast": "GET", "shipment-tracking": "GET", "reverse-logistics": "POST", "ai-assistant": "POST",
    "return-grading": "POST", "return-upload": "POST", "support-tickets": "GET",
}
API_VERSION = "v1"

def _endpoint(api: Dict[str, Any]) -> str:
    return f"/{api['service'].lower()}/{api['api_id']}/{API_VERSION}"

# Monthly request quota each API starts with
DEFAULT_QUOTAS = {
    "workspace-management": 5000, "usage-analytics": 2000, "product-catalog": 100000, "multi-seller-bidding": 20000,
    "demand-forecast": 5000, "shipment-tracking": 50000, "reverse-logistics": 10000, "ai-assistant": 20000,
    "return-grading": 5000, "return-upload": 10000, "support-tickets": 10000,
}

# Limits each API has besides requests: (key, label, unit, default, maximum). They differ per API.
RATE_LIMIT = ("rate_limit_per_min", "Rate limit", "requests / min", 60, 10000)
API_LIMITS: Dict[str, List[tuple]] = {
    "workspace-management": [("roles", "Roles", "roles", 5, 100), ("team_members", "Team members", "members", 10, 1000)],
    "usage-analytics": [("dashboards", "Dashboards", "dashboards", 10, 500), ("retention_months", "Data retention", "months", 12, 120)],
    "product-catalog": [("products", "Products", "products", 5000, 1000000), ("images_per_product", "Images per product", "images", 5, 50)],
    "multi-seller-bidding": [("bid_rooms", "Open bid rooms", "rooms", 20, 1000), ("sellers_per_room", "Sellers per room", "sellers", 25, 1000)],
    "demand-forecast": [("forecast_products", "Products forecast", "products", 500, 100000), ("horizon_days", "Forecast horizon", "days", 90, 730)],
    "shipment-tracking": [("tracked_shipments", "Tracked shipments", "per month", 5000, 1000000), ("carriers", "Carriers", "carriers", 5, 100)],
    "reverse-logistics": [("routing_rules", "Routing rules", "rules", 25, 1000), ("recovery_channels", "Recovery channels", "channels", 6, 50)],
    "ai-assistant": [("voice_minutes", "Voice minutes", "per month", 1000, 100000), ("languages", "Languages", "languages", 5, 50)],
    "return-grading": [("photos_per_return", "Photos per return", "photos", 6, 50), ("graded_per_month", "Items graded", "per month", 5000, 1000000)],
    "return-upload": [("max_file_mb", "Max file size", "MB", 10, 100), ("storage_gb", "Storage", "GB", 50, 10000)],
    "support-tickets": [("agents", "Support agents", "agents", 10, 1000), ("sla_hours", "Response target", "hours", 24, 720)],
}

def _limit_fields(api_id: str) -> List[Dict[str, Any]]:
    return [{"key": k, "label": label, "unit": unit, "default": default, "max": top}
            for k, label, unit, default, top in [*API_LIMITS.get(api_id, []), RATE_LIMIT]]

# What the Owner has changed for one consumer: {tenant_id: {api_id: {monthly_fee_usd, price_per_1k_requests_usd, request_quota}}}
API_OVERRIDES: Dict[str, Dict[str, Dict[str, Any]]] = {}
SETTING_KEYS = ("monthly_fee_usd", "price_per_1k_requests_usd", "request_quota")

# Preview entitlements. The Owner can switch any API on or off for any consumer at any time.
ENTITLEMENTS = {
    "t-001": set(ALL_API_IDS),
    "t-002": ALL_API_IDS - {"usage-analytics", "return-upload"},
    "t-003": {"workspace-management", "product-catalog", "multi-seller-bidding", "shipment-tracking"},
}

def _hash(password: str) -> str:
    return hashlib.sha256(("auracommerce-demo:" + password).encode("utf-8")).hexdigest()

# Demo accounts for preview mode. The account decides the portal; replace with real
# sign-in (for example Firebase Authentication) before any production use.
ACCOUNTS = {
    "admin@auracommerce.io": {"password_hash": _hash("Owner@123"), "user_id": "usr-101", "portal": "Owner"},
    "seller@greencycle.com": {"password_hash": _hash("Seller@123"), "user_id": "usr-102", "portal": "Consumer"},
    "customer@gmail.com": {"password_hash": _hash("Customer@123"), "user_id": "usr-103", "portal": "Customer"},
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

    def list_api_catalog(self) -> List[Dict[str, Any]]:
        return [{**api, "request_quota": DEFAULT_QUOTAS[api["api_id"]],
                 "method": API_METHODS[api["api_id"]], "endpoint": _endpoint(api)} for api in API_CATALOG]

    def get_api_settings(self, tenant_id: str) -> Dict[str, Dict[str, Any]]:
        """The fee, price and quota in force for each API: the defaults, with this consumer's changes on top."""
        overrides = API_OVERRIDES.get(tenant_id, {})
        return {
            api["api_id"]: {**{k: api[k] for k in SETTING_KEYS if k != "request_quota"},
                            "request_quota": DEFAULT_QUOTAS[api["api_id"]],
                            **{k: v for k, v in overrides.get(api["api_id"], {}).items() if k != "limits"},
                            "limits": {**{f["key"]: f["default"] for f in _limit_fields(api["api_id"])},
                                       **overrides.get(api["api_id"], {}).get("limits", {})}}
            for api in API_CATALOG
        }

    def update_api_settings(self, tenant_id: str, api_id: str, values: Dict[str, Any]) -> bool:
        if self.get_tenant(tenant_id) is None or api_id not in ALL_API_IDS:
            return False
        current = API_OVERRIDES.setdefault(tenant_id, {}).setdefault(api_id, {})
        current.update({k: v for k, v in values.items() if k in SETTING_KEYS})
        if values.get("limits"):
            current.setdefault("limits", {}).update(values["limits"])
        return True

    def get_limit_fields(self, api_id: str) -> List[Dict[str, Any]]:
        return _limit_fields(api_id)

    def reset_api_settings(self, tenant_id: str, api_id: str) -> bool:
        if self.get_tenant(tenant_id) is None or api_id not in ALL_API_IDS:
            return False
        API_OVERRIDES.get(tenant_id, {}).pop(api_id, None)
        return True

    def enabled_api_ids(self, tenant_id: str) -> set:
        return set(ENTITLEMENTS.get(tenant_id, set()))

    def set_api_enabled(self, tenant_id: str, api_id: str, enabled: bool) -> bool:
        """Switches one API on or off for one consumer. False if the consumer or API is unknown."""
        if self.get_tenant(tenant_id) is None or api_id not in ALL_API_IDS:
            return False
        entitlements = ENTITLEMENTS.setdefault(tenant_id, set())
        if enabled:
            entitlements.add(api_id)
        else:
            entitlements.discard(api_id)
        return True

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
                "role": account["portal"], "tenant": user["tenant"]}

cloud_sql_maas = CloudSQLMaaS()
