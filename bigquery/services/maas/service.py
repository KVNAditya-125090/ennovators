"""
BigQuery - MaaS (Management as a Service)
The platform's own figures, for the Owner: spend against the $120 three-month budget, history over time, each consumer's
usage and the telemetry of the Google Cloud services.

Where each figure comes from:
  hosting cost and budget    the table hosting_cost_daily in BigQuery (a billing export fills it in production)
  calls, response time, errors, usage    the audit log in Cloud SQL, one line for every call the gate handled
  queries and tickets        Firestore (the visitor queries and the tickets consumers raise with the Owner)
  telemetry                  Cloud Logging, the real log lines of the project's Google Cloud services
"""

import datetime
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, List, Tuple

from cloud_sql import db
from cloud_sql.services.maas import cloud_sql_maas
from cloud_sql.services.maas.endpoints import endpoint_registry
from firestore import store

log = logging.getLogger("lakshmi.bigquery")

PROJECT = os.environ.get("GCP_PROJECT", "ennovators")
DATASET = "lakshmi_analytics"
BUDGET_USD = 120.00          # three months, 40% of the trial credit
BUDGET_DAYS = 90

# period -> (days covered, days per point)
PERIODS = {"7d": (7, 1), "30d": (30, 1), "3m": (90, 7), "6m": (180, 7), "12m": (360, 30)}

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

# Storage and AI allowances of one consumer's workspace
WORKSPACE_QUOTA = {"ai_requests_quota": 5000, "storage_quota_gb": 10}

_client = None
_lock = threading.Lock()
_cache: Dict[str, Tuple[float, Any]] = {}

def client():
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                from google.cloud import bigquery
                _client = bigquery.Client(project=PROJECT)
    return _client

def cached(key: str, seconds: int, make: Callable[[], Any]) -> Any:
    """Keeps an answer for a short while, so a busy dashboard does not run the same query again and again."""
    now = time.time()
    hit = _cache.get(key)
    if hit and hit[0] > now:
        return hit[1]
    value = make()
    _cache[key] = (now + seconds, value)
    return value

def query(sql: str, **params: Any) -> List[Dict[str, Any]]:
    from google.cloud import bigquery
    config = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter(k, "INT64" if isinstance(v, int) else "STRING", v) for k, v in params.items()])
    return [dict(r) for r in client().query(sql, job_config=config).result()]

def hosting_cost_by_day(days: int) -> Dict[str, float]:
    """Hosting cost in USD for each of the last days: {date: usd}. Empty when nothing has been loaded."""
    def make():
        try:
            rows = query(f"SELECT CAST(day AS STRING) AS day, SUM(usd) AS usd FROM `{PROJECT}.{DATASET}.hosting_cost_daily` "
                         "WHERE day >= DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY) GROUP BY day", days=days)
            return {r["day"]: float(r["usd"]) for r in rows}
        except Exception:
            log.exception("could not read the hosting cost")
            return {}
    return cached(f"hosting:{days}", 120, make)

class BigQueryMaaS:
    def __init__(self):
        self.provider_status = "BigQuery, Cloud SQL and Cloud Logging"

    # ---- budget ----
    def get_budget_status(self) -> Dict[str, Any]:
        spent = round(sum(hosting_cost_by_day(BUDGET_DAYS).values()), 2)
        used = spent / BUDGET_USD * 100
        def state(threshold: int) -> str:
            return "REACHED" if used >= threshold else "OK"
        return {
            "budget_limit_usd": BUDGET_USD,
            "spent_to_date_usd": spent,
            "remaining_usd": round(BUDGET_USD - spent, 2),
            "percentage_used": round(used, 2),
            "alerts": [
                {"threshold": "50%", "status": state(50)},
                {"threshold": "75%", "status": state(75)},
                {"threshold": "90%", "status": state(90)},
                {"threshold": "100% (budget cap)", "status": state(100)},
            ]
        }

    def get_hosting_plan(self) -> List[Dict[str, Any]]:
        total = sum(amount for _, amount in HOSTING_PLAN)
        return [{"name": name, "planned_usd": amount, "share": amount / total} for name, amount in HOSTING_PLAN]

    # ---- history ----
    def get_platform_history(self, period: str, month_revenue: float, month_hosting_cost: float, month_requests: int, consumer_count: int = 0) -> List[Dict[str, Any]]:
        """Revenue, hosting cost, requests, response time, uptime, errors, queries and consumers over time.

        Calls, response time and errors are counted from the audit log. Revenue is the month's billing spread over the
        days by their share of the calls. Hosting cost is read from BigQuery."""
        days, step = PERIODS[period]
        today = datetime.date.today()
        daily = {r["d"]: r for r in db.rows("""SELECT (at AT TIME ZONE 'UTC')::date::text AS d, count(*)::int AS n,
                       count(*) FILTER (WHERE status >= 500 AND status <> 501)::int AS errors,
                       coalesce(percentile_cont(0.95) WITHIN GROUP (ORDER BY ms), 0)::float AS p95
                FROM audit_log WHERE at > now() - make_interval(days => :d) AND status <> 501 GROUP BY 1""", d=days + 1)}
        thirty = db.one("SELECT count(*)::int AS n FROM audit_log WHERE at > now() - interval '30 days' AND status < 400")["n"]
        per_request = month_revenue / thirty if thirty else 0.0
        cost = hosting_cost_by_day(days + 1)
        received, answered, first, resolution = {}, {}, {}, {}
        for q in store.rows("queries", "query_id", scope="global", newest_first=True):
            received[q["received"]] = received.get(q["received"], 0) + 1
            if q["status"] != "New":
                answered[q["received"]] = answered.get(q["received"], 0) + 1
            if q.get("first_response_hours") is not None:
                first.setdefault(q["received"], []).append(q["first_response_hours"])
        for t in store.rows("platform_tickets", "ticket_id", scope="global", newest_first=True):
            if t.get("resolution_hours") is not None:
                resolution.setdefault(t["opened"], []).append(t["resolution_hours"])

        points = []
        dates = [(today - datetime.timedelta(days=ago)).isoformat() for ago in range(days - 1, -1, -1)]
        for start in range(0, len(dates), step):
            group = dates[start:start + step]
            rows = [daily[d] for d in group if d in daily]
            n = sum(r["n"] for r in rows)
            errors = sum(r["errors"] for r in rows)
            p95 = (sum(r["p95"] * r["n"] for r in rows) / n / 1000) if n else 0.0
            f = [h for d in group for h in first.get(d, [])]
            res = [h for d in group for h in resolution.get(d, [])]
            points.append({
                "date": group[-1], "revenue": round(sum(daily.get(d, {"n": 0})["n"] for d in group) * per_request, 2),
                "hosting_cost": round(sum(cost.get(d, 0.0) for d in group), 2), "requests": n, "p95_seconds": round(p95, 2),
                "uptime_pct": round(100 - (errors / n * 100), 2) if n else 100.0, "errors_pct": round(errors / n * 100, 3) if n else 0.0,
                "queries_received": sum(received.get(d, 0) for d in group), "queries_answered": sum(answered.get(d, 0) for d in group),
                "first_response_hours": round(sum(f) / len(f), 1) if f else 0.0, "resolution_hours": round(sum(res) / len(res), 1) if res else 0.0,
                "consumers": consumer_count})
        return points

    # ---- telemetry ----
    def get_gcp_logs(self, limit: int = 60) -> List[Dict[str, Any]]:
        """The latest log lines of the project's Google Cloud services together, newest first (from Cloud Logging)."""
        def make():
            try:
                return _read_logs(limit)
            except Exception:
                log.exception("could not read Cloud Logging")
                return []
        return cached(f"logs:{limit}", 30, make)

    # ---- usage ----
    def get_endpoint_usage(self, tenant_id: str, categories: Dict[str, str]) -> Dict[str, int]:
        """Calls in the last 30 days to each endpoint ({path: category}) for one consumer, counted from the audit log."""
        counts = endpoint_registry.call_counts(tenant_id, 30)
        return {path: counts.get(path, 0) for path in categories}

    def record_call(self, tenant_id: str, path: str) -> None:
        """Kept for the gate: the audit log is the record of every call, so there is nothing more to count here."""

    def get_workspace_usage(self, tenant_name: str) -> Dict[str, Any]:
        """Use of the workspace's AI and storage allowances."""
        tenant = cloud_sql_maas.get_tenant_by_name(tenant_name)
        used_ai, used_gb = 0, 0.0
        if tenant is not None:
            ai_paths = {e["path"] for e in endpoint_registry.list_endpoints() if e["ai"]}
            used_ai = sum(n for p, n in endpoint_registry.call_counts(tenant["tenant_id"], 30).items() if p in ai_paths)
            used_gb = _storage_gb(tenant["tenant_id"])
        return {"ai_requests_used": used_ai, "storage_used_gb": round(used_gb, 3), **WORKSPACE_QUOTA}

def _storage_gb(tenant_id: str) -> float:
    def make():
        try:
            from cloud_storage import media_store
            return sum(b.size or 0 for b in media_store.bucket().list_blobs(prefix=tenant_id + "/")) / 1e9
        except Exception:
            log.exception("could not measure storage")
            return 0.0
    return cached(f"storage:{tenant_id}", 300, make)

# The services in the project and how their log entries are recognised
SERVICE_BY_RESOURCE = {"cloud_run_revision": ("cloud-run", "Cloud Run"), "cloudsql_database": ("cloud-sql", "Cloud SQL"),
                       "bigquery_resource": ("bigquery", "BigQuery"), "gcs_bucket": ("cloud-storage", "Cloud Storage"),
                       "aiplatform.googleapis.com/Endpoint": ("vertex-ai", "Vertex AI"), "build": ("cloud-build", "Cloud Build")}
LEVEL = {"DEBUG": "info", "INFO": "info", "NOTICE": "info", "DEFAULT": "info", "WARNING": "warning", "ERROR": "error", "CRITICAL": "error", "ALERT": "error", "EMERGENCY": "error"}

def _read_logs(limit: int) -> List[Dict[str, Any]]:
    from google.cloud import logging as cloud_logging
    since = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    kinds = " OR ".join(f'resource.type="{k}"' for k in SERVICE_BY_RESOURCE)
    entries = cloud_logging.Client(project=PROJECT).list_entries(filter_=f'timestamp>="{since}" AND ({kinds})', order_by=cloud_logging.DESCENDING, page_size=limit, max_results=limit)
    lines = []
    for e in entries:
        service_id, service = SERVICE_BY_RESOURCE.get(e.resource.type, ("other", e.resource.type))
        request = getattr(e, "http_request", None) or {}
        payload = e.payload
        if isinstance(payload, dict):
            message = payload.get("message") or payload.get("textPayload") or str(payload)[:200]
        else:
            message = str(payload or "")
        if request and not message:
            message = f"{request.get('requestMethod', '')} {request.get('status', '')}"
        lines.append({"timestamp": e.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"), "service_id": service_id, "service": service,
                      "level": LEVEL.get(str(e.severity or "DEFAULT").upper(), "info"), "method": request.get("requestMethod", ""),
                      "endpoint": (request.get("requestUrl") or "").replace("https://", "")[:120], "description": f"{service} log entry",
                      "message": message[:240]})
    return lines

bigquery_maas = BigQueryMaaS()
