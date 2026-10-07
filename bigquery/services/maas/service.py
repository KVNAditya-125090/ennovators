"""
BigQuery - MaaS (Management as a Service)
Billing-export query behind the $120 3-month budget cap (also a Looker Studio source).
"""

from typing import Dict, Any, List
import datetime
import hashlib
import random

# period -> (days covered, days per point)
PERIODS = {"7d": (7, 1), "30d": (30, 1), "3m": (90, 7), "6m": (180, 7), "12m": (360, 30)}

def _noise(seed: str, spread: float) -> float:
    """Repeatable pseudo-random factor between 1 - spread and 1 + spread."""
    unit = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    return 1 + (unit * 2 - 1) * spread

# Queries from the home page in a typical month (preview): received, and answered by email or phone
MONTH_QUERIES_RECEIVED = 12
MONTH_QUERIES_ANSWERED = 9

# Planned hosting cost by component (3-month plan, USD). Names are neutral on purpose.
HOSTING_PLAN = [
    ("AI models", 24.00),
    ("Database", 30.00),
    ("AI assistant", 22.00),
    ("API and agents", 6.00),
    ("Network", 4.00),
    ("Build and registry", 3.00),
    ("Logging and monitoring", 3.00),
    ("Storage", 2.00),
]

# Preview metering: API requests this month, per consumer
API_USAGE = {
    "t-001": {"workspace-management": 820, "usage-analytics": 310, "product-catalog": 48200, "multi-seller-bidding": 9400, "demand-forecast": 1450,
              "shipment-tracking": 22100, "reverse-logistics": 3100, "ai-assistant": 5200, "return-grading": 1800, "return-upload": 2100, "support-tickets": 4300},
    "t-002": {"workspace-management": 410, "usage-analytics": 90, "product-catalog": 15200, "multi-seller-bidding": 3800, "demand-forecast": 620,
              "shipment-tracking": 8900, "reverse-logistics": 2400, "ai-assistant": 1900, "return-grading": 950, "return-upload": 700, "support-tickets": 1500},
    "t-003": {"workspace-management": 190, "product-catalog": 6100, "multi-seller-bidding": 1700, "demand-forecast": 220,
              "shipment-tracking": 3200, "ai-assistant": 400, "support-tickets": 650},
}

# Preview usage per tenant workspace
WORKSPACE_USAGE = {
    "GreenCycle Refurbishers": {"ai_requests_used": 1240, "ai_requests_quota": 5000, "storage_used_gb": 3.4, "storage_quota_gb": 10},
    "NextLife Electronics": {"ai_requests_used": 610, "ai_requests_quota": 2500, "storage_used_gb": 1.1, "storage_quota_gb": 5},
    "Aura Eco Retail": {"ai_requests_used": 2960, "ai_requests_quota": 10000, "storage_used_gb": 6.8, "storage_quota_gb": 20},
}
DEFAULT_USAGE = {"ai_requests_used": 0, "ai_requests_quota": 1000, "storage_used_gb": 0.0, "storage_quota_gb": 2}

# Live endpoint health from the request logs; anything not listed is healthy
DEFAULT_HEALTH = {"state": "active", "latency_ms": 180}
API_HEALTH = {
    "multi-seller-bidding": {"latency_ms": 420},
    "demand-forecast": {"state": "slow", "latency_ms": 2450},
    "ai-assistant": {"latency_ms": 890},
    "return-grading": {"state": "slow", "latency_ms": 3120},
    "shipment-tracking": {"latency_ms": 260},
}

# The Google Cloud services behind the platform; a service that is responding slowly logs more warnings
GCP_SERVICES = [
    {"service_id": "cloud-run", "name": "Cloud Run", "status": "active"},
    {"service_id": "cloud-sql", "name": "Cloud SQL", "status": "active"},
    {"service_id": "bigquery", "name": "BigQuery", "status": "active"},
    {"service_id": "firestore", "name": "Firestore", "status": "active"},
    {"service_id": "vertex-ai", "name": "Vertex AI", "status": "slow"},
    {"service_id": "cloud-storage", "name": "Cloud Storage", "status": "active"},
    {"service_id": "firebase-hosting", "name": "Firebase Hosting", "status": "active"},
]

# The Google Cloud endpoints each service is called on: (method, address, what it does)
PROJECT = "auracommerce-360"
GCP_ENDPOINTS = {
    "cloud-run": {
        "serve": ("GET", "https://aura-api.a.run.app/api/v1/*", "Public address of the platform API"),
        "admin": ("GET", f"run.googleapis.com/v2/projects/{PROJECT}/locations/us-central1/services/aura-api", "Reads and scales the API service"),
    },
    "cloud-sql": {
        "connect": ("POST", f"sqladmin.googleapis.com/v1/projects/{PROJECT}/instances/aura-db:generateEphemeralCert", "Short-lived certificate used to connect to the database"),
        "backup": ("POST", f"sqladmin.googleapis.com/v1/projects/{PROJECT}/instances/aura-db/backupRuns", "Takes a backup of the database"),
    },
    "bigquery": {
        "query": ("POST", f"bigquery.googleapis.com/bigquery/v2/projects/{PROJECT}/queries", "Runs a SQL query"),
        "load": ("POST", f"bigquery.googleapis.com/upload/bigquery/v2/projects/{PROJECT}/jobs", "Loads the billing export"),
        "insert": ("POST", f"bigquery.googleapis.com/bigquery/v2/projects/{PROJECT}/datasets/metering/tables/api_usage/insertAll", "Writes usage metering rows"),
    },
    "firestore": {
        "read": ("POST", f"firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents:batchGet", "Reads documents"),
        "write": ("POST", f"firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents:commit", "Writes documents"),
        "listen": ("POST", f"firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents:listen", "Streams live changes to the app"),
        "index": ("POST", f"firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/collectionGroups/tickets/indexes", "Builds an index"),
    },
    "vertex-ai": {
        "forecast": ("POST", f"us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/us-central1/endpoints/forecast:predict", "Runs the demand forecast model"),
        "grading": ("POST", f"us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/us-central1/endpoints/grading:predict", "Grades a returned item from its photos"),
        "assistant": ("POST", f"us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/us-central1/publishers/google/models/gemini:generateContent", "Writes the assistant's replies"),
    },
    "cloud-storage": {
        "upload": ("POST", "storage.googleapis.com/upload/storage/v1/b/aura-returns/o", "Uploads a return photo"),
        "sign": ("POST", f"iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/aura-storage@{PROJECT}.iam.gserviceaccount.com:signBlob", "Signs a short-lived upload link"),
        "lifecycle": ("PATCH", "storage.googleapis.com/storage/v1/b/aura-returns", "Updates the bucket's lifecycle rules"),
    },
    "firebase-hosting": {
        "serve": ("GET", f"{PROJECT}.web.app/", "Serves the web app"),
        "release": ("POST", f"firebasehosting.googleapis.com/v1beta1/sites/{PROJECT}/releases", "Publishes a new release"),
        "rewrite": ("GET", f"{PROJECT}.web.app/api/**", "Passes API calls on to Cloud Run"),
    },
}

# (level, message, the endpoint that was called)
GCP_LOG_MESSAGES = {
    "cloud-run": [
        ("info", "Request completed with 200 in 112 ms", "serve"), ("info", "Request completed with 201 in 240 ms", "serve"),
        ("info", "Instance started and ready for traffic", "admin"), ("info", "Scaled to 3 instances", "admin"),
        ("warning", "Cold start took 1,850 ms", "serve"), ("warning", "CPU above 80% for 2 minutes", "admin"),
        ("warning", "Request completed with 429, rate limit reached", "serve"), ("error", "Request failed with 500", "serve"),
    ],
    "cloud-sql": [
        ("info", "Checkpoint completed", "connect"), ("info", "Automated backup finished", "backup"), ("info", "18 connections open", "connect"),
        ("warning", "Slow query took 1,240 ms", "connect"), ("warning", "Connection pool above 80%", "connect"), ("error", "Connection reset by a client", "connect"),
    ],
    "bigquery": [
        ("info", "Query finished, 1.2 GB scanned", "query"), ("info", "Billing export loaded", "load"), ("info", "Usage metering table refreshed", "insert"),
        ("warning", "Query took 9.4 s", "query"), ("warning", "Daily scan above 80% of the plan", "query"), ("error", "Query failed: resources exceeded", "query"),
    ],
    "firestore": [
        ("info", "Read 120 documents", "read"), ("info", "Wrote ticket update", "write"), ("info", "Index build complete", "index"),
        ("warning", "Hot document, writes are slowing", "write"), ("warning", "Listener reconnected", "listen"), ("error", "Write rejected: contention", "write"),
    ],
    "vertex-ai": [
        ("info", "Forecast prediction finished in 2.1 s", "forecast"), ("info", "Return grading finished in 2.8 s", "grading"), ("info", "Assistant reply generated", "assistant"),
        ("warning", "Prediction took 3.4 s, over the target", "forecast"), ("warning", "Quota above 60% for the day", "assistant"), ("error", "Prediction failed: model timed out", "grading"),
    ],
    "cloud-storage": [
        ("info", "Object uploaded, 2.1 MB", "upload"), ("info", "Signed upload link issued", "sign"), ("info", "Lifecycle rule moved 40 objects", "lifecycle"),
        ("warning", "Upload retried after a timeout", "upload"), ("warning", "Bucket size above 80% of the plan", "lifecycle"), ("error", "Upload rejected: file too large", "upload"),
    ],
    "firebase-hosting": [
        ("info", "Served index.html from cache", "serve"), ("info", "New release is live", "release"), ("info", "Asset served in 38 ms", "serve"),
        ("warning", "Request for a missing file", "serve"), ("warning", "Bandwidth above 80% of the daily plan", "rewrite"), ("error", "Rewrite to the API failed with 502", "rewrite"),
    ],
}

class BigQueryMaaS:
    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def get_budget_status(self) -> Dict[str, Any]:
        limit, spent = 120.00, 18.45
        return {
            "budget_limit_usd": limit,
            "spent_to_date_usd": spent,
            "remaining_usd": round(limit - spent, 2),
            "percentage_used": round(spent / limit * 100, 2),
            "alerts": [
                {"threshold": "50%", "status": "OK"},
                {"threshold": "75%", "status": "OK"},
                {"threshold": "90%", "status": "OK"},
                {"threshold": "100% (Kill Switch)", "status": "ARMED"}
            ]
        }

    def get_platform_history(self, period: str, month_revenue: float, month_hosting_cost: float, month_requests: int, consumer_count: int = 3) -> List[Dict[str, Any]]:
        """Revenue, hosting cost, requests, response time, uptime, errors and consumers over time.

        Preview data: a repeatable series shaped so the most recent 30 days add up to the
        current month's figures, with earlier days lower as the platform grew.
        """
        days, step = PERIODS[period]
        span = max(days, 30)
        today = datetime.date.today()
        records = []
        for ago in range(span - 1, -1, -1):
            day = today - datetime.timedelta(days=ago)
            growth = max(0.15, 1 - ago / 450)
            weekday = 0.85 if day.weekday() >= 5 else 1.0
            records.append({
                "date": day,
                "ago": ago,
                "revenue": growth * weekday * _noise(f"rev{day}", 0.12),
                "hosting_cost": (0.9 + 0.1 * growth) * _noise(f"cost{day}", 0.06),
                "requests": growth * weekday * _noise(f"req{day}", 0.15),
                "p95_seconds": 1.4 * _noise(f"p95{day}", 0.25),
                "uptime_pct": 100 - abs(_noise(f"up{day}", 1.0) - 1) * 0.2,
                "errors_pct": 0.15 * _noise(f"err{day}", 0.8),
                "queries_received": growth * weekday * _noise(f"tko{day}", 0.5),
                "queries_answered": growth * weekday * _noise(f"tkr{day}", 0.5),
                "first_response_hours": 2.2 * _noise(f"frh{day}", 0.4),
                "resolution_hours": 20.0 * _noise(f"rsh{day}", 0.35),
                "consumers": max(1, consumer_count - (1 if ago > 120 else 0) - (1 if ago > 240 else 0)),
            })

        def scale(key: str, target: float) -> float:
            recent = sum(r[key] for r in records if r["ago"] < 30)
            return target / recent if recent else 0.0

        k_rev = scale("revenue", month_revenue)
        k_cost = scale("hosting_cost", month_hosting_cost)
        k_req = scale("requests", month_requests)
        k_open = scale("queries_received", MONTH_QUERIES_RECEIVED)
        k_resolved = scale("queries_answered", MONTH_QUERIES_ANSWERED)

        window = records[-days:]
        groups = [window[max(0, end - step):end] for end in range(len(window), 0, -step)][::-1]
        points = []
        cum = {"open": 0.0, "resolved": 0.0}  # round running totals so small daily counts still add up exactly
        done = {"open": 0, "resolved": 0}
        for group in groups:
            cum["open"] += sum(r["queries_received"] for r in group) * k_open
            cum["resolved"] += sum(r["queries_answered"] for r in group) * k_resolved
            opened = int(round(cum["open"])) - done["open"]
            resolved = int(round(cum["resolved"])) - done["resolved"]
            done["open"] += opened
            done["resolved"] += resolved
            points.append({
                "date": group[-1]["date"].isoformat(),
                "revenue": round(sum(r["revenue"] for r in group) * k_rev, 2),
                "hosting_cost": round(sum(r["hosting_cost"] for r in group) * k_cost, 2),
                "requests": int(round(sum(r["requests"] for r in group) * k_req)),
                "p95_seconds": round(sum(r["p95_seconds"] for r in group) / len(group), 2),
                "uptime_pct": round(sum(r["uptime_pct"] for r in group) / len(group), 2),
                "errors_pct": round(sum(r["errors_pct"] for r in group) / len(group), 3),
                "queries_received": opened,
                "queries_answered": resolved,
                "first_response_hours": round(sum(r["first_response_hours"] for r in group) / len(group), 1),
                "resolution_hours": round(sum(r["resolution_hours"] for r in group) / len(group), 1),
                "consumers": group[-1]["consumers"],
            })
        return points

    def get_hosting_plan(self) -> List[Dict[str, Any]]:
        total = sum(amount for _, amount in HOSTING_PLAN)
        return [{"name": name, "planned_usd": amount, "share": amount / total} for name, amount in HOSTING_PLAN]

    def get_api_health(self, api_id: str) -> Dict[str, Any]:
        """How an endpoint is responding right now: its state (active, slow or failing) and its 95th percentile latency in ms."""
        return {**DEFAULT_HEALTH, **API_HEALTH.get(api_id, {})}

    def get_gcp_logs(self, limit: int = 60) -> List[Dict[str, Any]]:
        """The latest log lines of all the Google Cloud services together, newest first."""
        now = datetime.datetime.utcnow().replace(second=0, microsecond=0)
        lines = []
        for service in GCP_SERVICES:
            rng = random.Random(service["service_id"])  # the same sample every time
            slow = service["status"] != "active"
            weights = {"info": 80, "warning": 35 if slow else 15, "error": 6 if slow else 2}
            messages = GCP_LOG_MESSAGES[service["service_id"]]
            minutes = 0
            for _ in range(40):
                minutes += rng.randint(1, 9)
                level = rng.choices(list(weights), weights=list(weights.values()))[0]
                _, message, endpoint = rng.choice([m for m in messages if m[0] == level])
                method, address, description = GCP_ENDPOINTS[service["service_id"]][endpoint]
                lines.append({
                    "timestamp": (now - datetime.timedelta(minutes=minutes)).isoformat() + "Z",
                    "service_id": service["service_id"], "service": service["name"], "level": level,
                    "method": method, "endpoint": address, "description": description, "message": message,
                })
        return sorted(lines, key=lambda line: line["timestamp"], reverse=True)[:limit]

    def get_api_usage(self, tenant_id: str) -> Dict[str, int]:
        """API requests this month for one consumer, from the metering table."""
        return dict(API_USAGE.get(tenant_id, {}))

    def get_workspace_usage(self, tenant_name: str) -> Dict[str, Any]:
        """Usage against the per-workspace AI and storage quotas."""
        return dict(WORKSPACE_USAGE.get(tenant_name, DEFAULT_USAGE))

bigquery_maas = BigQueryMaaS()
