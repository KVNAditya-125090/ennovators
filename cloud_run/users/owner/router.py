"""
Owner Router - the developer of the product.
Lists every consumer, shows their details, which APIs are enabled and what they cost,
and lets the Owner switch any API on or off for any consumer at any time.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from cloud_run.services.maas import get_system_health
from cloud_run.users.owner.schemas import ApiToggle, ApiSettings, QueryUpdate
from cloud_sql.users import owner as cloud_sql
from bigquery.users import owner as bigquery
from firestore.users import owner as firestore

router = APIRouter(prefix="/api/v1/owner", tags=["Owner"])

PERIOD_DAYS = {"7d": 7, "30d": 30, "3m": 90, "6m": 180, "12m": 360}
SERVICE_ORDER = ("MaaS", "PaaS", "TaaS", "SaaS")

def _api_rows(tenant_id: str) -> List[Dict[str, Any]]:
    """Every API in the catalog with this consumer's switch, usage and cost."""
    enabled = cloud_sql.enabled_api_ids(tenant_id)
    usage = bigquery.get_api_usage(tenant_id)
    settings = cloud_sql.get_api_settings(tenant_id)
    rows = []
    for api in cloud_sql.get_api_catalog():
        now = settings[api["api_id"]]
        fields = cloud_sql.get_limit_fields(api["api_id"])
        health = bigquery.get_api_health(api["api_id"])
        on = api["api_id"] in enabled
        requests = usage.get(api["api_id"], 0) if on else 0
        cost = round(now["monthly_fee_usd"] + requests / 1000 * now["price_per_1k_requests_usd"], 2) if on else 0.0
        rows.append({
            **api,
            **now,  # the fee, price and quota in force for this consumer
            "default_monthly_fee_usd": api["monthly_fee_usd"],
            "default_price_per_1k_requests_usd": api["price_per_1k_requests_usd"],
            "default_request_quota": api["request_quota"],
            "limit_fields": [{**f, "value": now["limits"][f["key"]]} for f in fields],
            "customised": any(now[k] != api[k] for k in ("monthly_fee_usd", "price_per_1k_requests_usd", "request_quota"))
                          or any(now["limits"][f["key"]] != f["default"] for f in fields),
            "endpoint_status": health["state"] if on else "stopped",
            "latency_ms": health["latency_ms"] if on else None,
            "enabled": on, "requests_this_month": requests, "cost_usd": cost
        })
    return rows

def _summary(tenant: Dict[str, Any]) -> Dict[str, Any]:
    rows = _api_rows(tenant["tenant_id"])
    return {
        **{k: v for k, v in tenant.items() if k != "users_count"},  # headcount is a privacy matter: the Owner does not see it
        "enabled_apis": sum(1 for r in rows if r["enabled"]),
        # a service counts as opted for when at least one of its APIs is switched on
        "opted_services": [code for code in SERVICE_ORDER if any(r["enabled"] and r["service"] == code for r in rows)],
        "total_apis": len(rows),
        "monthly_cost_usd": round(sum(r["cost_usd"] for r in rows), 2)
    }

def _detail(tenant: Dict[str, Any]) -> Dict[str, Any]:
    rows = _api_rows(tenant["tenant_id"])
    return {
        "consumer": _summary(tenant),
        "profile": cloud_sql.get_profile(tenant["tenant_id"]),
        "usage": bigquery.get_workspace_usage(tenant["name"]),
        "apis": rows,
        "tickets": sorted((t for t in firestore.list_platform_tickets() if t["tenant_id"] == tenant["tenant_id"]),
                          key=lambda t: t["opened"], reverse=True),
        "monthly_cost_usd": round(sum(r["cost_usd"] for r in rows), 2)
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
    """Every API on the platform: how its endpoint is doing and how many consumers use it."""
    tenants = cloud_sql.list_tenants()
    rows = []
    for api in cloud_sql.get_api_catalog():
        health = bigquery.get_api_health(api["api_id"])
        opted = [t for t in tenants if api["api_id"] in cloud_sql.enabled_api_ids(t["tenant_id"])]
        rows.append({
            **api,
            "endpoint_status": health["state"], "latency_ms": health["latency_ms"],
            "consumers_opted": len(opted), "total_consumers": len(tenants),
            "requests_this_month": sum(bigquery.get_api_usage(t["tenant_id"]).get(api["api_id"], 0) for t in opted),
        })
    return {"apis": rows}

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
    # how many of all the platform's APIs are responding normally, whether or not any consumer has opted in
    states = [bigquery.get_api_health(api["api_id"])["state"] for api in cloud_sql.get_api_catalog()]
    return {
        "health": {**get_system_health(), "apis_working": states.count("active"), "apis_total": len(states)},
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
    consumer_rows = {t["tenant_id"]: _api_rows(t["tenant_id"]) for t in tenants}
    month_revenue = round(sum(r["cost_usd"] for rows in consumer_rows.values() for r in rows), 2)
    month_requests = sum(r["requests_this_month"] for rows in consumer_rows.values() for r in rows)
    month_hosting = bigquery.get_budget_status()["spent_to_date_usd"]

    points = bigquery.get_platform_history(period, month_revenue, month_hosting, month_requests, len(tenants))
    revenue = round(sum(p["revenue"] for p in points), 2)
    hosting = round(sum(p["hosting_cost"] for p in points), 2)
    margin = round(revenue - hosting, 2)

    def share(amount: float) -> float:
        return round(revenue * amount / month_revenue, 2) if month_revenue else 0.0

    by_api: Dict[str, Dict[str, Any]] = {}
    for rows in consumer_rows.values():
        for r in rows:
            entry = by_api.setdefault(r["api_id"], {"api_id": r["api_id"], "name": r["name"], "service": r["service"], "amount": 0.0})
            entry["amount"] += r["cost_usd"]

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
                {"name": t["name"], "enabled": sum(1 for r in consumer_rows[t["tenant_id"]] if r["enabled"]), "total": len(consumer_rows[t["tenant_id"]])}
                for t in tenants
            ]
        },
        "revenue_by_consumer": sorted(
            [{"name": t["name"], "revenue_usd": share(sum(r["cost_usd"] for r in consumer_rows[t["tenant_id"]]))} for t in tenants],
            key=lambda x: -x["revenue_usd"]),
        "revenue_by_api": sorted(
            [{"api_id": e["api_id"], "name": e["name"], "service": e["service"], "revenue_usd": share(e["amount"])} for e in by_api.values()],
            key=lambda x: -x["revenue_usd"])
    }

@router.get("/consumers/{tenant_id}")
def get_consumer(tenant_id: str) -> Dict[str, Any]:
    return _detail(_require_tenant(tenant_id))

@router.patch("/consumers/{tenant_id}/apis/{api_id}/settings")
def update_api_settings(tenant_id: str, api_id: str, settings: ApiSettings) -> Dict[str, Any]:
    """Change an API's fee, price per 1,000 requests or monthly quota for one consumer, or reset them to the defaults."""
    tenant = _require_tenant(tenant_id)
    if settings.reset:
        ok = cloud_sql.reset_api_settings(tenant_id, api_id)
    else:
        changes = settings.model_dump(exclude={"reset"}, exclude_none=True)
        if not changes:
            raise HTTPException(status_code=422, detail="Nothing to change")
        allowed = {f["key"]: f for f in cloud_sql.get_limit_fields(api_id)}
        for key, value in (changes.get("limits") or {}).items():
            if key not in allowed or not 0 <= value <= allowed[key]["max"]:
                raise HTTPException(status_code=422, detail=f"Invalid limit: {key}")
        ok = cloud_sql.update_api_settings(tenant_id, api_id, changes)
    if not ok:
        raise HTTPException(status_code=404, detail="API not found")
    return _detail(tenant)

@router.put("/consumers/{tenant_id}/apis/{api_id}")
def set_api(tenant_id: str, api_id: str, toggle: ApiToggle) -> Dict[str, Any]:
    tenant = _require_tenant(tenant_id)
    if not cloud_sql.set_api_enabled(tenant_id, api_id, toggle.enabled):
        raise HTTPException(status_code=404, detail="API not found")
    return _detail(tenant)
