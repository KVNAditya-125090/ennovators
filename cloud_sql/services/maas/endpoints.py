"""
Cloud SQL (PostgreSQL) - MaaS endpoint registry
The 409 endpoints of the platform, seeded from endpoint_catalog_v1.csv (never retyped), and which
of them each consumer has opted into with the Owner (the "purchased" gate).
"""

import csv
import datetime
from collections import deque
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from cloud_sql.services.maas.endpoint_params import parameters_for

CATALOG_FILE = Path(__file__).with_name("endpoint_catalog_v1.csv")
SERVICE_CODES = {"maas": "MaaS", "paas": "PaaS", "taas": "TaaS", "saas": "SaaS"}
BASE_SERVICE = "MaaS"  # required by every consumer; opting into any other service includes it

# The category an endpoint is filed under: partner when a partner is involved, then intelligence when it
# uses AI, otherwise by its actor
CATEGORY_BY_ACTOR = {"Consumer root": "consumer", "Consumer staff": "consumer", "Customer": "customer", "System": "system"}
CATEGORIES = ("consumer", "customer", "partner", "intelligence", "system")

def _category(row: Dict[str, str]) -> Optional[str]:
    if row["actor"].startswith("Owner"):
        return None  # Owner roles: a consumer never sees these
    if row["actor"] == "Partner" or row["feature"] == "partner" or "partner link" in row["depends_on"]:
        return "partner"
    return "intelligence" if row["ai"] == "Yes" else CATEGORY_BY_ACTOR[row["actor"]]

# The HTTP method is not in the catalog; it follows from what the endpoint does
READ_VERBS = {"read", "list", "view", "find", "preview", "export", "scan"}

def _method(sub_category: str, parameters: List[Dict[str, Any]]) -> str:
    parts = sub_category.split("/")
    verb = "read" if parts[-1] in ("staff", "customer") and "read" in parts else parts[-1]  # e.g. order/read/staff
    if verb in READ_VERBS:
        return "POST" if any(p["type"] == "file" for p in parameters) else "GET"
    if verb == "update":
        return "PATCH"
    if verb == "set":
        return "PUT"
    if verb in ("remove", "revoke", "delete"):
        return "DELETE"
    return "POST"

# Automatic (System) jobs that belong to the platform itself, so the Owner runs and watches them.
# Every other System, AI and Partner endpoint works on one consumer's own data, so it sits with that consumer.
OWNER_RUN = {"/maas/owner-role-mail/invite/send/v1", "/maas/audit/log/write/v1"}

# Who starts an endpoint: a person, an automatic job, an AI model, or a partner company
RUNS_BY_ACTOR = {"System": "automatic", "AI": "ai", "Partner": "partner"}

def _load() -> List[Dict[str, Any]]:
    with CATALOG_FILE.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    endpoints = []
    for row in rows:
        actor = row["actor"]
        endpoints.append({
            "path": row["path"],
            "service": SERVICE_CODES[row["service"]],
            "feature": row["feature"],
            "sub_category": row["sub_category"],
            "version": row["version"],
            "actor": actor,
            "category": _category(row),
            "description": row["description"],
            "parameters": parameters_for(row["path"]),  # [] when the endpoint just returns its data
            "method": _method(row["sub_category"], parameters_for(row["path"])),
            "ai": row["ai"] == "Yes",
            "list_item": None if row["list_item"] == "-" else row["list_item"],
            "depends_on": [] if row["depends_on"] == "-" else [d.strip() for d in row["depends_on"].split(",")],
            # Owner roles run these on the Owner side, with the platform's own automatic jobs: a consumer does not buy them
            "owner_side": actor.startswith("Owner") or row["path"] in OWNER_RUN,
            "runs": RUNS_BY_ACTOR.get(actor, "person"),
        })
    return endpoints

ENDPOINTS: List[Dict[str, Any]] = _load()
ENDPOINT_BY_PATH = {e["path"]: e for e in ENDPOINTS}
SERVICE_ORDER = ("MaaS", "PaaS", "TaaS", "SaaS")

def _service_paths(service: str) -> Set[str]:
    return {e["path"] for e in ENDPOINTS if e["service"] == service and not e["owner_side"]}

# Preview entitlements, by endpoint path. Every consumer starts with the whole of the services it uses today.
ENDPOINT_ENTITLEMENTS: Dict[str, Set[str]] = {
    "t-001": set().union(*(_service_paths(s) for s in SERVICE_ORDER)),  # the one consumer: every service and endpoint
}

# What the Owner can set for each endpoint, per consumer. The Owner changes any of the three.
DEFAULT_RATE_LIMIT = 60       # calls per minute
MAX_RATE_LIMIT = 10000
MAX_MONTHLY_FEE = 10000.0     # USD
MAX_PRICE_PER_1K = 1000.0     # USD per 1,000 calls
# Starting price by category: (monthly fee USD, USD per 1,000 calls). Intelligence costs more to run.
DEFAULT_PRICES = {"intelligence": (0.50, 2.00)}
DEFAULT_PRICE = (0.10, 0.20)
SETTING_KEYS = ("rate_limit_per_min", "monthly_fee_usd", "price_per_1k_calls_usd")
SETTING_OVERRIDES: Dict[str, Dict[str, Dict[str, Any]]] = {}  # {tenant_id: {path: {setting: value}}}

def default_settings(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    fee, price = DEFAULT_PRICES.get(endpoint["category"], DEFAULT_PRICE)
    return {"rate_limit_per_min": DEFAULT_RATE_LIMIT, "monthly_fee_usd": fee, "price_per_1k_calls_usd": price}

# Every call that reached the gate: who, what, when and how it ended. The newest 2,000, in memory.
AUDIT_LOG: deque = deque(maxlen=2000)

class EndpointRegistry:
    def list_endpoints(self, service: Optional[str] = None) -> List[Dict[str, Any]]:
        return [dict(e) for e in ENDPOINTS if service is None or e["service"] == service]

    def enabled_paths(self, tenant_id: str) -> Set[str]:
        return set(ENDPOINT_ENTITLEMENTS.get(tenant_id, set()))

    def service_summary(self, tenant_id: str) -> Dict[str, Dict[str, Any]]:
        """For each service: how many of the endpoints a consumer can buy it has on, and whether it counts as opted."""
        on = ENDPOINT_ENTITLEMENTS.get(tenant_id, set())
        summary = {}
        for code in SERVICE_ORDER:
            paths = _service_paths(code)
            count = len(paths & on)
            summary[code] = {"code": code, "total": len(paths), "on": count, "opted": count > 0,
                             "owner_side": sum(1 for e in ENDPOINTS if e["service"] == code and e["owner_side"])}
        return summary

    def record_audit(self, tenant_id: Optional[str], path: str, method: str, status: int, code: str, ms: Optional[float] = None) -> None:
        AUDIT_LOG.appendleft({"at": datetime.datetime.utcnow().isoformat() + "Z", "tenant_id": tenant_id, "path": path,
                              "method": method, "status": status, "code": code, "ms": ms})

    def list_audit(self, tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        return [entry for entry in AUDIT_LOG if entry["tenant_id"] == tenant_id][:limit]

    def endpoint_settings(self, tenant_id: str) -> Dict[str, Dict[str, Any]]:
        """The settings in force for each endpoint: the defaults, with this consumer's changes on top."""
        overrides = SETTING_OVERRIDES.get(tenant_id, {})
        return {e["path"]: {**default_settings(e), **overrides.get(e["path"], {})} for e in ENDPOINTS}

    def update_settings(self, tenant_id: str, path: str, values: Dict[str, Any], reset: bool = False) -> str:
        """Changes some settings of one endpoint, or sets them all back to the defaults. Returns "ok", "unknown" or "owner_side"."""
        endpoint = ENDPOINT_BY_PATH.get(path)
        if endpoint is None:
            return "unknown"
        if endpoint["owner_side"]:
            return "owner_side"
        current = SETTING_OVERRIDES.setdefault(tenant_id, {}).setdefault(path, {})
        if reset:
            current.clear()
        defaults = default_settings(endpoint)
        for key, value in values.items():
            if key in SETTING_KEYS:
                if value == defaults[key]:
                    current.pop(key, None)  # back at the default: nothing to remember
                else:
                    current[key] = value
        if not current:
            SETTING_OVERRIDES[tenant_id].pop(path, None)
        return "ok"

    def set_endpoint_enabled(self, tenant_id: str, path: str, enabled: bool) -> str:
        """Opts one endpoint in or out. Returns "ok", "unknown", "owner_side" or "maas_required"."""
        endpoint = ENDPOINT_BY_PATH.get(path)
        if endpoint is None:
            return "unknown"
        if endpoint["owner_side"]:
            return "owner_side"
        on = ENDPOINT_ENTITLEMENTS.setdefault(tenant_id, set())
        if enabled:
            on.add(path)
            if endpoint["service"] != BASE_SERVICE and not on & _service_paths(BASE_SERVICE):
                on |= _service_paths(BASE_SERVICE)  # opting into any service includes maas
        else:
            # maas cannot be left empty while another service is in use
            if endpoint["service"] == BASE_SERVICE and path in on and len(on & _service_paths(BASE_SERVICE)) == 1 \
                    and any(on & _service_paths(s) for s in SERVICE_ORDER if s != BASE_SERVICE):
                return "maas_required"
            on.discard(path)
        return "ok"

    def set_service_enabled(self, tenant_id: str, service: str, enabled: bool) -> str:
        """Opts a whole service in or out (its base endpoints). Returns "ok", "unknown" or "maas_required"."""
        if service not in SERVICE_ORDER:
            return "unknown"
        on = ENDPOINT_ENTITLEMENTS.setdefault(tenant_id, set())
        if enabled:
            on |= _service_paths(service)
            on |= _service_paths(BASE_SERVICE)
        else:
            if service == BASE_SERVICE and any(on & _service_paths(s) for s in SERVICE_ORDER if s != BASE_SERVICE):
                return "maas_required"
            on -= _service_paths(service)
        return "ok"

endpoint_registry = EndpointRegistry()
