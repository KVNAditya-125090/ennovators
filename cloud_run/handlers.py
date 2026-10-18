"""
Cloud Run - endpoint handlers
What a call does once it has passed the gate, by catalog path. A handler takes the tenant and the call's
parameters and returns the response body. An endpoint with no handler here answers 501 not_implemented.
"""

from typing import Any, Callable, Dict

from bigquery.users import consumer as bigquery
from cloud_sql.services.maas import cloud_sql_maas
from cloud_run.ids import new_id
from firestore import store
from firestore.users import consumer as firestore
from firestore.users.consumer import operations as ops
from vertex_ai.users import consumer as vertex_ai
from cloud_run.ids import seed_id
from cloud_run import forecast_math, mapsupport

Handler = Callable[[Dict[str, Any], Dict[str, Any]], Any]
HANDLERS: Dict[str, Handler] = {}

def handles(path: str):
    def register(fn: Handler) -> Handler:
        HANDLERS[path] = fn
        return fn
    return register

@handles("/maas/user/staff/list/v1")
def list_staff(tenant, params):
    return {"staff": cloud_sql_maas.list_members(tenant["name"])}

@handles("/maas/root-account/settings/read/v1")
def read_settings(tenant, params):
    return ops.settings()

@handles("/maas/root-account/settings/update/v1")
def update_settings(tenant, params):
    return ops.update_settings(params)

@handles("/maas/role/read/v1")
def read_roles(tenant, params):
    return {"roles": ops.list_roles(tenant["tenant_id"])}

@handles("/maas/role/create/v1")
def create_role(tenant, params):
    return ops.create_role(tenant["tenant_id"], params["name"], params.get("description"))

@handles("/maas/role/update/v1")
def update_role(tenant, params):
    return ops.update_role(tenant["tenant_id"], params["role_id"], params.get("name"), params.get("description"))

@handles("/maas/role/deactivate/v1")
def deactivate_role(tenant, params):
    return ops.deactivate_role(tenant["tenant_id"], params["role_id"])

@handles("/paas/catalog/product/read/v1")
def read_products(tenant, params):
    return {"products": ops.list_products()}

@handles("/paas/catalog/product/create/v1")
def create_product(tenant, params):
    return ops.create_product(params)

@handles("/paas/catalog/product/update/v1")
def update_product(tenant, params):
    return ops.update_product(params)

@handles("/paas/catalog/product/archive/v1")
def archive_product(tenant, params):
    return ops.archive_product(params["product_id"])

@handles("/paas/inventory/stock/read/v1")
def read_stock(tenant, params):
    return {"stock": ops.read_stock(params.get("sku"))}

@handles("/paas/inventory/stock/update/v1")
def update_stock(tenant, params):
    return ops.update_stock(params["sku"], params["quantity"])

@handles("/paas/inventory/stock/adjust/v1")
def adjust_stock(tenant, params):
    return ops.adjust_stock(params["sku"], params["quantity_change"], params["reason"])

@handles("/paas/order/read/staff/v1")
def read_orders(tenant, params):
    return {"orders": ops.read_orders(params.get("status"))}

@handles("/paas/order/status/update/v1")
def update_order_status(tenant, params):
    return ops.update_order_status(params["order_id"], params["status"])

@handles("/taas/shipment/read/staff/v1")
def read_shipments(tenant, params):
    return {"shipments": ops.list_shipments(params.get("status"))}

@handles("/taas/shipment/create/v1")
def create_shipment(tenant, params):
    return ops.create_shipment(params["order_id"], params.get("carrier"))

@handles("/taas/shipment/status/update/v1")
def update_shipment_status(tenant, params):
    return ops.update_shipment_status(params["shipment_id"], params["status"])

@handles("/taas/shipment/cancel/v1")
def cancel_shipment(tenant, params):
    return ops.cancel_shipment(params["shipment_id"], params.get("reason"))

@handles("/saas/ticket/read/staff/v1")
def read_tickets(tenant, params):
    return {"tickets": ops.read_tickets(params.get("status"))}

@handles("/saas/ticket/reply/staff/v1")
def reply_ticket(tenant, params):
    return ops.reply_ticket(params["ticket_id"], params["message"], params.get("author"))

@handles("/saas/ticket/status/update/v1")
def update_ticket_status(tenant, params):
    return ops.update_ticket_status(params["ticket_id"], params["status"])

@handles("/saas/ticket/close/v1")
def close_ticket(tenant, params):
    return ops.close_ticket(params["ticket_id"], params.get("resolution"))

@handles("/saas/return/request/read/v1")
def read_returns(tenant, params):
    return {"returns": ops.read_returns(params.get("status")), "policy": ops.return_policy()}

@handles("/saas/return/request/approve/v1")
def approve_return(tenant, params):
    return ops.approve_return(params["return_id"])

@handles("/saas/return/request/reject/v1")
def reject_return(tenant, params):
    return ops.reject_return(params["return_id"], params["reason"])

@handles("/saas/return/refund/issue/v1")
def issue_refund(tenant, params):
    return ops.issue_refund(params["return_id"], params["amount"])

@handles("/saas/return/policy/set/v1")
def set_return_policy(tenant, params):
    return ops.set_return_policy(params["window_days"], params.get("conditions"), params["refund_method"])

def _explain_forecast(history, days, reorder_point):
    """Plain-language reasons for the forecast, worked out from the numbers it shows."""
    if not days:
        return {"summary": "There is no sales history yet, so there is nothing to forecast.", "reasons": []}
    demand = [d["predicted_demand"] for d in days]
    half = len(demand) // 2
    first, second = sum(demand[:half]) / max(half, 1), sum(demand[half:]) / max(len(demand) - half, 1)
    change = round((second - first) / first * 100) if first else 0
    peak = max(days, key=lambda d: d["predicted_demand"])
    reasons = []
    if history:
        usual = round(sum(h["units_sold"] for h in history) / len(history))
        reasons.append(f"Built from your last {len(history)} days of sales, which averaged {usual} units a day.")
    reasons.append(f"Demand is expected to {'rise' if change > 3 else 'fall' if change < -3 else 'hold steady'}"
                   f"{f' by about {abs(change)}%' if abs(change) > 3 else ''} from the first week to the second.")
    reasons.append(f"The busiest day is {peak['date']}, with about {peak['predicted_demand']} units.")
    reasons.append(forecast_math.describe(history, days, reorder_point))
    return {"summary": reasons[1], "reasons": reasons}

@handles("/paas/forecast/demand/read/v1")
def read_forecast(tenant, params):
    sku = params.get("sku") or ""
    history = bigquery.get_demand_history(sku)
    days = vertex_ai.forecast_demand(sku, history)
    reorder_point = forecast_math.reorder_point(history, days)
    return {"sku": sku, "forecast_period": "14 Days", "recommended_reorder_point": reorder_point, "daily_forecast": days,
            "explanation": _explain_forecast(history, days[:14], reorder_point)}

# ---- MaaS: company account, usage and billing ----
from bigquery.services.maas import bigquery_maas
from cloud_sql.services.maas.endpoints import endpoint_registry

def _usage_rows(tenant):
    """Every endpoint this consumer has opted into, with this month's calls and what it costs."""
    tid = tenant["tenant_id"]
    on = endpoint_registry.enabled_paths(tid)
    settings = endpoint_registry.endpoint_settings(tid)
    endpoints = [e for e in endpoint_registry.list_endpoints() if e["path"] in on and not e["owner_side"]]
    calls = bigquery_maas.get_endpoint_usage(tid, {e["path"]: e["category"] for e in endpoints})
    rows = []
    for e in endpoints:
        s = settings[e["path"]]
        n = calls[e["path"]]
        rows.append({"path": e["path"], "service": e["service"], "description": e["description"], "calls": n,
                     "monthly_fee_usd": s["monthly_fee_usd"], "price_per_1k_calls_usd": s["price_per_1k_calls_usd"],
                     "cost_usd": round(s["monthly_fee_usd"] + n / 1000 * s["price_per_1k_calls_usd"], 2)})
    return rows

def _by_service(rows):
    out = {}
    for r in rows:
        s = out.setdefault(r["service"], {"service": r["service"], "endpoints": 0, "calls": 0, "cost_usd": 0.0})
        s["endpoints"] += 1
        s["calls"] += r["calls"]
        s["cost_usd"] = round(s["cost_usd"] + r["cost_usd"], 2)
    return [out[c] for c in ("MaaS", "PaaS", "TaaS", "SaaS") if c in out]

@handles("/maas/root-account/read/v1")
def read_account(tenant, params):
    profile = cloud_sql_maas.get_profile(tenant["tenant_id"]) or {}
    return {"name": tenant["name"], "type": tenant["type"], "status": tenant["status"], **profile}

@handles("/maas/analytics/dashboard/read/v1")
def read_dashboard(tenant, params):
    rows = _usage_rows(tenant)
    return {"endpoints_opted": len(rows), "endpoints_total": sum(1 for e in endpoint_registry.list_endpoints() if not e["owner_side"]), "calls": sum(r["calls"] for r in rows), "cost_usd": round(sum(r["cost_usd"] for r in rows), 2),
            "services": _by_service(rows)}

@handles("/maas/analytics/usage/read/v1")
def read_usage(tenant, params):
    rows = [r for r in _usage_rows(tenant) if not params.get("endpoint_path") or r["path"] == params["endpoint_path"]]
    return {"usage": sorted(({k: r[k] for k in ("path", "service", "description", "calls")} for r in rows), key=lambda r: -r["calls"])}

@handles("/maas/billing/usage/read/v1")
def read_billing_usage(tenant, params):
    rows = [r for r in _usage_rows(tenant) if not params.get("endpoint_path") or r["path"] == params["endpoint_path"]]
    return {"charges": sorted(rows, key=lambda r: -r["cost_usd"]), "total_usd": round(sum(r["cost_usd"] for r in rows), 2)}

@handles("/maas/billing/invoice/read/v1")
def read_invoices(tenant, params):
    rows = _usage_rows(tenant)
    profile = cloud_sql_maas.get_profile(tenant["tenant_id"]) or {}
    billing = profile.get("billing", {})
    return {"invoices": [{"invoice_id": seed_id("invoice:" + tenant["tenant_id"]), "period": "This month", "status": "Open", "due": billing.get("next_invoice"),
                          "total_usd": round(sum(r["cost_usd"] for r in rows), 2), "by_service": _by_service(rows)}]}

# ---- MaaS: role holders, role access and the root's mail log ----
def _consumer_path(tenant, path):
    """A role can only be given an endpoint the workspace has opted into that staff may call."""
    endpoint = next((e for e in endpoint_registry.list_endpoints() if e["path"] == path), None)
    if endpoint is None or path not in endpoint_registry.enabled_paths(tenant["tenant_id"]):
        raise LookupError(f"{path} is not an endpoint your workspace has opted into")
    if endpoint["actor"] not in ("Consumer staff", "System", "AI", "Partner"):
        raise ValueError("Only endpoints that staff run (or the automatic, AI and partner ones) can be given to a role")

@handles("/maas/role-mail/list/v1")
def list_role_mails(tenant, params):
    return {"role_mails": ops.list_role_mails(tenant["tenant_id"])}

@handles("/maas/role-mail/assign/v1")
def assign_role_mail(tenant, params):
    return ops.assign_role_mail(tenant["tenant_id"], params["role_id"], params["mail"])

@handles("/maas/role-mail/remove/v1")
def remove_role_mail(tenant, params):
    return ops.remove_role_mail(tenant["tenant_id"], params["role_id"], params["mail"])

@handles("/maas/role/permission/read/v1")
def read_role_permissions(tenant, params):
    return {"role_id": params["role_id"], "permissions": ops.read_role_permissions(tenant["tenant_id"], params["role_id"])}

@handles("/maas/role/permission/assign/v1")
def assign_role_permission(tenant, params):
    _consumer_path(tenant, params["endpoint_path"])
    return ops.assign_role_permission(tenant["tenant_id"], params["role_id"], params["endpoint_path"])

@handles("/maas/role/permission/revoke/v1")
def revoke_role_permission(tenant, params):
    return ops.revoke_role_permission(tenant["tenant_id"], params["role_id"], params["endpoint_path"])

@handles("/maas/notification/root-mail/log/read/v1")
def read_mail_log(tenant, params):
    return {"mails": ops.read_mail_log(tenant["tenant_id"])}


# ---- TaaS: routing returns, delivery rules and insights ----
def _route(kind):
    def handler(tenant, params):
        return ops.route_return(params["return_id"], kind)
    return handler

for _kind in ops.RETURN_ROUTES:
    HANDLERS[f"/taas/reverse/route/{_kind}/assign/v1"] = _route(_kind)

@handles("/taas/reverse/pickup/schedule/v1")
def schedule_pickup(tenant, params):
    return ops.schedule_return_pickup(params["return_id"], params["pickup_at"], params.get("carrier"))

@handles("/taas/delivery/rules/set/v1")
def set_delivery_rules(tenant, params):
    return ops.set_delivery_rules(params["options"], params.get("cutoff_time"), params.get("regions"))

@handles("/taas/locale/service-area/set/v1")
def set_service_area(tenant, params):
    return ops.set_service_area(params["mode"], params["regions"])

@handles("/taas/analytics/delivery/read/v1")
def read_delivery_analytics(tenant, params):
    shipments = firestore.track_shipments()
    done = [s for s in shipments if s["status"] == "delivered"]
    return {"shipments": len(shipments), "delivered": len(done), "on_time_pct": None, "avg_days": None, "rules": ops.delivery_rules(), "service_area": ops.service_area(),
            "by_carrier": [{"carrier": c, "shipments": sum(1 for s in shipments if s["carrier"] == c)} for c in sorted({s["carrier"] for s in shipments})]}

@handles("/taas/insights/delivery/read/v1")
def read_delivery_insights(tenant, params):
    return {"patterns": []}  # patterns need delivery history to work from

@handles("/taas/impact/report/read/v1")
def read_transport_impact(tenant, params):
    shipments = firestore.track_shipments()
    return {"co2_saved_kg": round(sum(s.get("co2_saved_kg", 0) for s in shipments if s["status"] != "cancelled"), 1), "electric_share_pct": None, "returns_recovered": sum(1 for r in ops._returns() if r.get("route"))}

# ---- MaaS: the template and how roles see their workspace ----
@handles("/maas/interface/template/read/v1")
def read_template(tenant, params):
    return ops.read_template(tenant["tenant_id"])

@handles("/maas/interface/template/create/v1")
def create_template(tenant, params):
    return ops.create_template(tenant["tenant_id"], params["name"], params["layout"], params.get("branding"), params.get("sections"))

@handles("/maas/interface/template/update/v1")
def update_template(tenant, params):
    return ops.update_template(tenant["tenant_id"], params.get("layout"), params.get("branding"), params.get("sections"))

@handles("/maas/interface/template/role-view/update/v1")
def update_role_view(tenant, params):
    return ops.set_role_view(tenant["tenant_id"], params["role_id"], params["view"])

@handles("/maas/interface/template/preview/v1")
def preview_template(tenant, params):
    t = ops.read_template(tenant["tenant_id"])
    paths = {s["path"] if isinstance(s, dict) else s for s in t.get("sections", [])}
    shown = [e for e in endpoint_registry.list_endpoints() if e["path"] in paths]
    return {**t, "resolved": [{"path": e["path"], "description": e["description"], "service": e["service"]} for e in shown]}

@handles("/maas/interface/template/publish/v1")
def publish_template(tenant, params):
    return ops.publish_template(tenant["tenant_id"], params.get("version_note"))

# ---- TaaS: AI delivery planning (route, vehicle, delivery time, slots), each with its explanation ----
from vertex_ai.services.taas import planner  # noqa: E402

def _shipment(shipment_id):
    from firestore.services.taas import firestore_taas
    return ops._find(firestore_taas.list_shipments(), "shipment_id", shipment_id)

@handles("/taas/route/shortest/calculate/v1")
def calculate_shortest_route(tenant, params):
    """Road distance, time and the route line between two places (Google Maps; a straight-line estimate when Maps is off)."""
    return mapsupport.road_route(params["origin"], params["destination"])

@handles("/taas/locale/address/validate/v1")
def validate_address(tenant, params):
    return mapsupport.check_address(params["address"] if isinstance(params["address"], dict) else {"address": str(params["address"])}, params["country"])

@handles("/taas/route/optimize/recommend/v1")
def recommend_route(tenant, params):
    return planner.recommend_route(_shipment(params["shipment_id"]), params.get("objective"), params.get("stops"))

@handles("/taas/vehicle/recommend/v1")
def recommend_vehicle(tenant, params):
    return planner.recommend_vehicle(_shipment(params["shipment_id"]), params.get("weight_kg"), params.get("volume_l"))

@handles("/taas/delivery/eta/predict/v1")
def predict_eta(tenant, params):
    return planner.predict_eta(_shipment(params["shipment_id"]))

@handles("/taas/delivery/slot/recommend/v1")
def recommend_slots(tenant, params):
    return planner.recommend_slots(_shipment(params["shipment_id"]), params.get("from"))

@handles("/taas/explain/decision/read/v1")
def explain_decision(tenant, params):
    return planner.get_decision(params["decision_id"])

@handles("/taas/recommendation/accept/v1")
def accept_recommendation(tenant, params):
    d = planner.get_decision(params["decision_id"])
    return planner.apply(d["decision_id"], _shipment(d["shipment_id"]), None, None, ops.ACTOR.get())

@handles("/taas/recommendation/override/v1")
def override_recommendation(tenant, params):
    d = planner.get_decision(params["decision_id"])
    return planner.apply(d["decision_id"], _shipment(d["shipment_id"]), params["choice"], params["reason"], ops.ACTOR.get())

# ---- MaaS: stores, what the workspace bought, its customers and its audit log ----
STORE_FIELDS = ("name", "address", "city", "country", "latitude", "longitude", "opening_hours")

def _stores_rows():
    return store.rows("stores", "store_id")

def _one_store(store_id):
    found = next((s for s in _stores_rows() if s["store_id"] == store_id), None)
    if found is None:
        raise LookupError(f"No store {store_id}")
    return found

@handles("/maas/location/store/read/v1")
def read_stores(tenant, params):
    return {"stores": _stores_rows()}

@handles("/maas/location/store/create/v1")
def create_store(tenant, params):
    row = {"store_id": new_id(), "active": True, **{k: params.get(k) for k in STORE_FIELDS}}
    if any(s["name"].lower() == str(row["name"]).lower() for s in _stores_rows()):
        raise ValueError(f"A store called {row['name']} already exists")
    _stores_rows().append(row)
    return row

@handles("/maas/location/store/update/v1")
def update_store(tenant, params):
    row = _one_store(params["store_id"])
    row.update({k: params[k] for k in STORE_FIELDS if params.get(k) not in (None, "")})
    return row

@handles("/maas/location/store/deactivate/v1")
def deactivate_store(tenant, params):
    row = _one_store(params["store_id"])
    row["active"] = False
    return row

@handles("/maas/endpoint/purchased/list/v1")
def list_purchased(tenant, params):
    on = endpoint_registry.enabled_paths(tenant["tenant_id"])
    return {"endpoints": [{"path": e["path"], "service": e["service"], "description": e["description"], "category": e["category"], "actor": e["actor"]}
                          for e in endpoint_registry.list_endpoints() if e["path"] in on], "count": len(on)}

def _customers(tenant):
    return [{"customer_id": u["user_id"], "name": u["name"], "email": u["email"], "account_type": "individual"}
            for u in cloud_sql_maas.list_members(tenant["name"]) if u["role"].startswith("Customer")]

@handles("/maas/user/customer/list/v1")
def list_customers(tenant, params):
    return {"customers": _customers(tenant)}

@handles("/maas/user/customer/read/v1")
def read_customer(tenant, params):
    found = next((c for c in _customers(tenant) if c["customer_id"] == params["customer_id"]), None)
    if found is None:
        raise LookupError(f"No customer {params['customer_id']}")
    mine = [o for o in ops._orders() if o.get("customer_email") == found["email"]]
    return {**found, "orders": len(mine), "spent_usd": round(sum(o["total"] for o in mine if o["status"] != "cancelled"), 2)}

@handles("/maas/audit/log/read/v1")
def read_audit(tenant, params):
    rows = endpoint_registry.list_audit(tenant["tenant_id"], 500)
    if params.get("endpoint_path"):
        rows = [r for r in rows if r["path"] == params["endpoint_path"]]
    if params.get("from"):
        rows = [r for r in rows if r["at"][:10] >= str(params["from"])]
    if params.get("to"):
        rows = [r for r in rows if r["at"][:10] <= str(params["to"])]
    return {"entries": rows[:200], "count": len(rows)}

# ---- Analytics, impact and insight screens, worked out from the consumer's own records ----
from cloud_run import insights  # noqa: E402
insights.install(HANDLERS)

# ---- Dynamic pricing and the AI bidding hand-off ----
from cloud_run import bid_flow, commerce, green_route, impact, pricing, rules, translation  # noqa: E402
for _module in (pricing, bid_flow, translation, rules, commerce, impact, green_route):
    _module.install(HANDLERS)

# ---- The Customer portal: stand-in handlers for every Customer-side endpoint (real where there is sample data) ----
from cloud_run.customer_handlers import register_customer_handlers  # noqa: E402
register_customer_handlers(HANDLERS)

# ---- Everything else an Owner or Consumer role can do: preview stand-ins until the backend is integrated ----
from cloud_run.preview import register_previews  # noqa: E402  (after every real handler, so real ones win)
register_previews(HANDLERS)
