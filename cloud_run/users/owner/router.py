"""
Owner Router - the developer of the product.
Lists every consumer, shows their details, which endpoints each has opted into and what they cost,
and lets the Owner opt any consumer in or out of any endpoint or service at any time.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from urllib.parse import unquote
from cloud_run.access import is_owner
from typing import Dict, Any, List
from cloud_run.services.maas import get_system_health
from cloud_run.users.owner.schemas import QueryUpdate, EndpointToggle, ServiceToggle, EndpointSettings
from cloud_sql.users import owner as cloud_sql
from bigquery.users import owner as bigquery
from firestore.users import owner as firestore

def require_owner(x_user_email: str = Header(None)) -> None:
    """Every Owner call must come from a signed-in Owner (Manager, Developer or Operator: all have the same access)."""
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Sign in as an Owner to use this.")
    if not is_owner(unquote(x_user_email)):
        raise HTTPException(status_code=403, detail="Only the Owner can use this.")

router = APIRouter(prefix="/api/v1/owner", tags=["Owner"], dependencies=[Depends(require_owner)])

PERIOD_DAYS = {"7d": 7, "30d": 30, "3m": 90, "6m": 180, "12m": 360}
SERVICE_ORDER = ("MaaS", "PaaS", "TaaS", "SaaS")

def _endpoint_rows(tenant_id: str) -> List[Dict[str, Any]]:
    """Every endpoint a consumer can buy, with its settings, this month's calls and what it costs. Only opted endpoints are billed."""
    on = cloud_sql.enabled_endpoint_paths(tenant_id)
    settings = cloud_sql.endpoint_settings(tenant_id)
    endpoints = [e for e in cloud_sql.list_endpoints() if not e["owner_side"]]
    usage = bigquery.get_endpoint_usage(tenant_id, {e["path"]: e["category"] for e in endpoints})
    rows = []
    for e in endpoints:
        now = settings[e["path"]]
        opted = e["path"] in on
        calls = usage[e["path"]] if opted else 0
        cost = round(now["monthly_fee_usd"] + calls / 1000 * now["price_per_1k_calls_usd"], 2) if opted else 0.0
        rows.append({**e, **now, "enabled": opted, "calls_this_month": calls, "cost_usd": cost})
    return rows

def _service_figures(tenant_id: str) -> Dict[str, Dict[str, Any]]:
    """For each service: the endpoints opted, and the calls and cost this month."""
    figures = cloud_sql.endpoint_service_summary(tenant_id)
    rows = _endpoint_rows(tenant_id)
    for code in SERVICE_ORDER:
        mine = [r for r in rows if r["service"] == code]
        figures[code] = {**figures[code], "calls": sum(r["calls_this_month"] for r in mine), "cost_usd": round(sum(r["cost_usd"] for r in mine), 2)}
    return figures

def _summary(tenant: Dict[str, Any]) -> Dict[str, Any]:
    figures = _service_figures(tenant["tenant_id"])
    return {
        **{k: v for k, v in tenant.items() if k != "users_count"},  # headcount is a privacy matter: the Owner does not see it
        "enabled_apis": sum(v["on"] for v in figures.values()),
        # a service counts as opted for when at least one of its endpoints is opted into
        "opted_services": [code for code in SERVICE_ORDER if figures[code]["opted"]],
        "total_apis": sum(v["total"] for v in figures.values()),
        "monthly_cost_usd": round(sum(v["cost_usd"] for v in figures.values()), 2)
    }

def _detail(tenant: Dict[str, Any]) -> Dict[str, Any]:
    figures = _service_figures(tenant["tenant_id"])
    return {
        "consumer": _summary(tenant),
        "profile": cloud_sql.get_profile(tenant["tenant_id"]),
        "usage": bigquery.get_workspace_usage(tenant["name"]),
        "endpoint_services": list(figures.values()),
        "tickets": sorted((t for t in firestore.list_platform_tickets() if t["tenant_id"] == tenant["tenant_id"]),
                          key=lambda t: t["opened"], reverse=True),
        "monthly_cost_usd": round(sum(v["cost_usd"] for v in figures.values()), 2)
    }

def _queries_summary(queries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The current state of the queries visitors have sent from the home page."""
    answered = [q["first_response_hours"] for q in queries if q["first_response_hours"] is not None]
    return {
        "open": sum(1 for q in queries if q["status"] != "Closed"),
        "new": sum(1 for q in queries if q["status"] == "New"),
        "avg_first_response_hours": round(sum(answered) / len(answered), 1) if answered else 0.0
    }

def _require_tenant(tenant_id: str) -> Dict[str, Any]:
    tenant = cloud_sql.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Consumer not found")
    return tenant

@router.get("/apis")
def list_platform_apis() -> Dict[str, Any]:
    """Every endpoint of the catalog, how it is doing, and how many consumers have opted into it."""
    from cloud_run.health import endpoint_health, health_summary
    tenants = cloud_sql.list_tenants()
    opted = {t["tenant_id"]: cloud_sql.enabled_endpoint_paths(t["tenant_id"]) for t in tenants}
    health = endpoint_health()
    return {"apis": [{**e, "health": health[e["path"]], "consumers_opted": sum(1 for paths in opted.values() if e["path"] in paths),
                      "total_consumers": len(tenants)} for e in cloud_sql.list_endpoints()],
            "summary": health_summary()}

@router.get("/telemetry")
def list_telemetry_logs(level: str = Query("all", pattern="^(all|error|warning|info)$")) -> Dict[str, Any]:
    """The latest log lines of every Google Cloud service together, optionally only errors or warnings."""
    status = {"info": "Success", "warning": "Warning", "error": "Failed"}
    logs = [{**entry, "status": status[entry["level"]]} for entry in bigquery.get_gcp_logs()]
    counts = {name: sum(1 for entry in logs if entry["level"] == name) for name in ("error", "warning", "info")}
    return {"logs": logs if level == "all" else [entry for entry in logs if entry["level"] == level], "counts": counts}

@router.get("/queries")
def list_queries() -> Dict[str, Any]:
    """Every query visitors have sent from the home page, newest first."""
    queries = sorted(firestore.list_queries(), key=lambda q: (q["received"], q["query_id"]), reverse=True)
    return {"queries": queries, "summary": _queries_summary(queries)}

@router.patch("/queries/{query_id}")
def update_query(query_id: str, update: QueryUpdate) -> Dict[str, Any]:
    """Move a query along once the team has replied by email or phone."""
    query = firestore.update_query(query_id, update.status)
    if query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return query

@router.get("/overview")
def get_overview() -> Dict[str, Any]:
    consumers = [_summary(t) for t in cloud_sql.list_tenants()]
    # how every catalog endpoint is doing, from the calls the gate handled (cloud_run/health.py)
    from cloud_run.health import health_summary
    return {
        "health": {**get_system_health(), **health_summary()},
        "budget": bigquery.get_budget_status(),
        "consumers": consumers,
        "support": _queries_summary(firestore.list_queries()),
        "total_monthly_cost_usd": round(sum(c["monthly_cost_usd"] for c in consumers), 2)
    }

def _queries_analytics(points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Query figures for the selected period."""
    queries = firestore.list_queries()
    return {
        "received": sum(p["queries_received"] for p in points),
        "answered": sum(p["queries_answered"] for p in points),
        "avg_first_response_hours": round(sum(p["first_response_hours"] for p in points) / len(points), 1),
        "summary": _queries_summary(queries)
    }

@router.get("/analytics")
def get_analytics(period: str = Query("30d", pattern="^(7d|30d|3m|6m|12m)$")) -> Dict[str, Any]:
    """History for the selected period. The overview cards show the current values; this shows how they changed."""
    tenants = cloud_sql.list_tenants()
    figures = {t["tenant_id"]: _service_figures(t["tenant_id"]) for t in tenants}
    month_revenue = round(sum(v["cost_usd"] for f in figures.values() for v in f.values()), 2)
    month_requests = sum(v["calls"] for f in figures.values() for v in f.values())
    month_hosting = bigquery.get_budget_status()["spent_to_date_usd"]

    points = bigquery.get_platform_history(period, month_revenue, month_hosting, month_requests, len(tenants))
    revenue = round(sum(p["revenue"] for p in points), 2)
    hosting = round(sum(p["hosting_cost"] for p in points), 2)
    margin = round(revenue - hosting, 2)

    def share(amount: float) -> float:
        return round(revenue * amount / month_revenue, 2) if month_revenue else 0.0

    return {
        "period": period,
        "points": points,
        "totals": {
            "revenue_usd": revenue,
            "hosting_cost_usd": hosting,
            "margin_usd": margin,
            "margin_pct": round(margin / revenue * 100, 1) if revenue else 0.0,
            "requests": sum(p["requests"] for p in points),
            "avg_p95_seconds": round(sum(p["p95_seconds"] for p in points) / len(points), 2),
            "avg_uptime_pct": round(sum(p["uptime_pct"] for p in points) / len(points), 2),
            "avg_errors_pct": round(sum(p["errors_pct"] for p in points) / len(points), 2),
            "days": PERIOD_DAYS[period]
        },
        "budget": bigquery.get_budget_status(),
        "support": _queries_analytics(points),
        "hosting_by_component": [
            {"name": c["name"], "cost_usd": round(hosting * c["share"], 2), "planned_usd": c["planned_usd"]}
            for c in bigquery.get_hosting_plan()
        ],
        "health_components": get_system_health()["components"],
        "consumers": {
            "count": len(tenants),
            "active": sum(1 for t in tenants if t["status"] == "Active"),
            "by_type": [{"name": name, "count": sum(1 for t in tenants if t["type"] == name)} for name in sorted({t["type"] for t in tenants})],
            "apis_enabled": [
                {"name": t["name"], "enabled": sum(v["on"] for v in figures[t["tenant_id"]].values()), "total": sum(v["total"] for v in figures[t["tenant_id"]].values())}
                for t in tenants
            ]
        },
        "revenue_by_consumer": sorted(
            [{"name": t["name"], "revenue_usd": share(sum(v["cost_usd"] for v in figures[t["tenant_id"]].values()))} for t in tenants],
            key=lambda x: -x["revenue_usd"]),
        "revenue_by_service": sorted(
            [{"service": code, "revenue_usd": share(sum(f[code]["cost_usd"] for f in figures.values()))} for code in SERVICE_ORDER],
            key=lambda x: -x["revenue_usd"])
    }

@router.get("/consumers/{tenant_id}")
def get_consumer(tenant_id: str) -> Dict[str, Any]:
    return _detail(_require_tenant(tenant_id))

ENDPOINT_ERRORS = {
    "unknown": (404, "Endpoint or service not found"),
    "owner_side": (422, "This endpoint runs on the Owner side and is not bought by a consumer"),
    "maas_required": (409, "MaaS cannot be switched off while another service is in use"),
}

def _endpoint_listing(tenant_id: str, service: str) -> Dict[str, Any]:
    """One service's endpoints for one consumer, with what is opted into."""
    on = cloud_sql.enabled_endpoint_paths(tenant_id)
    rows = [{**r, "defaults": cloud_sql.endpoint_defaults(r)} for r in _endpoint_rows(tenant_id) if r["service"] == service]  # Owner-side endpoints are not the consumer's
    return {"service": service, "summary": cloud_sql.endpoint_service_summary(tenant_id)[service],
            "limits": {"rate_limit_per_min": cloud_sql.MAX_RATE_LIMIT, "monthly_fee_usd": cloud_sql.MAX_MONTHLY_FEE, "price_per_1k_calls_usd": cloud_sql.MAX_PRICE_PER_1K},
            "service_figures": _service_figures(tenant_id)[service], "endpoints": rows}

def _check(result: str) -> None:
    if result != "ok":
        status, detail = ENDPOINT_ERRORS[result]
        raise HTTPException(status_code=status, detail=detail)

@router.get("/consumers/{tenant_id}/services/{service}/endpoints")
def list_consumer_endpoints(tenant_id: str, service: str) -> Dict[str, Any]:
    """Every endpoint of one service, and which of them this consumer has opted into."""
    _require_tenant(tenant_id)
    if service not in SERVICE_ORDER:
        raise HTTPException(status_code=404, detail="Service not found")
    return _endpoint_listing(tenant_id, service)

@router.put("/consumers/{tenant_id}/endpoints")
def set_endpoint(tenant_id: str, toggle: EndpointToggle) -> Dict[str, Any]:
    """Opt one endpoint in or out. Opting into a non-MaaS endpoint includes MaaS."""
    _require_tenant(tenant_id)
    _check(cloud_sql.set_endpoint_enabled(tenant_id, toggle.path, toggle.enabled))
    endpoint = next(e for e in cloud_sql.list_endpoints() if e["path"] == toggle.path)
    return _endpoint_listing(tenant_id, endpoint["service"])

@router.put("/consumers/{tenant_id}/services/{service}")
def set_service(tenant_id: str, service: str, toggle: ServiceToggle) -> Dict[str, Any]:
    """Opt a whole service in or out. Opting into any service other than MaaS includes MaaS."""
    _require_tenant(tenant_id)
    _check(cloud_sql.set_service_enabled(tenant_id, service, toggle.enabled))
    return _endpoint_listing(tenant_id, service)

@router.patch("/consumers/{tenant_id}/endpoints/settings")
def update_endpoint_settings(tenant_id: str, settings: EndpointSettings) -> Dict[str, Any]:
    """Change one endpoint's rate limit and price for one consumer, or reset them to the defaults."""
    _require_tenant(tenant_id)
    changes = settings.model_dump(exclude={"path", "reset"}, exclude_none=True)
    if not changes and not settings.reset:
        raise HTTPException(status_code=422, detail="Nothing to change")
    _check(cloud_sql.update_endpoint_settings(tenant_id, settings.path, changes, settings.reset))
    endpoint = next(e for e in cloud_sql.list_endpoints() if e["path"] == settings.path)
    return _endpoint_listing(tenant_id, endpoint["service"])

@router.get("/consumers/{tenant_id}/audit")
def read_audit_log(tenant_id: str, limit: int = Query(100, ge=1, le=500)) -> Dict[str, Any]:
    """The latest calls that reached the gate for one consumer, allowed or refused, newest first."""
    _require_tenant(tenant_id)
    return {"entries": cloud_sql.list_audit(tenant_id, limit)}


# ---- The Owner's own features from the catalog (owner-side endpoints) ----
# They run on the Owner side, so the consumer gate refuses them. Until their handlers are built they use the preview
# stand-ins (cloud_run/preview.py): a change is recorded and a read shows what was recorded.
@router.get("/features")
def list_owner_features() -> Dict[str, Any]:
    """Every owner-side endpoint, with its parameters, for the Owner console's Workspace pages."""
    return {"features": [e for e in cloud_sql.list_endpoints() if e["owner_side"]]}

@router.api_route("/features/run/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def run_owner_feature(path: str, request: Request, x_user_email: str = Header(None)) -> Dict[str, Any]:
    from cloud_run import gate, preview
    from cloud_run.access import find_user
    endpoint = next((e for e in cloud_sql.list_endpoints() if e["path"] == "/" + path and e["owner_side"]), None)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="No Owner feature at this path")
    if request.method != endpoint["method"]:
        raise HTTPException(status_code=405, detail=f"Use {endpoint['method']} for this feature")
    body = None
    if not gate.endpoint_is_read(request.method):
        try:
            body = await request.json()
        except ValueError:
            body = None
    params = gate._coerce(endpoint, dict(request.query_params) if gate.endpoint_is_read(request.method) else (body if isinstance(body, dict) else {}))
    missing = gate._missing(endpoint, params)
    if missing:
        raise HTTPException(status_code=422, detail={"code": "invalid_request", "message": "Missing required parameters: " + ", ".join(missing)})
    user = find_user(unquote(x_user_email)) or {}
    return preview.run("owner", endpoint, params, actor=user.get("name"))
