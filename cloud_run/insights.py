"""
Cloud Run - insights
The analytics, impact, scorecard and review screens of a consumer, worked out from its own records (orders, shipments,
tickets, returns, reviews and the audit log). Nothing here is typed in: when there are no records the figures are zero.

Two figures are assumptions, and say so: the energy of an AI request, and the carbon of a delivery that was not made by
an electric vehicle (used as the baseline an electric delivery is compared with).
"""

import collections
import datetime
from typing import Any, Callable, Dict, List

from cloud_sql.services.maas.endpoints import endpoint_registry
from firestore import store
from firestore.services.paas import firestore_paas
from firestore.services.taas import firestore_taas
from firestore.users.consumer import operations as ops

AI_WH_PER_REQUEST = 0.3     # assumption: watt-hours for one AI request
BASELINE_KG_PER_DELIVERY = 2.4  # assumption: kg of CO2e for a conventional diesel delivery
SALE_STATUSES = ("paid", "shipped", "delivered")

def _sales():
    return [o for o in ops._orders() if o["status"] in SALE_STATUSES]

def _lines(order: Dict[str, Any]) -> List[Dict[str, Any]]:
    return order.get("lines") or []

def _by_product() -> Dict[str, Dict[str, Any]]:
    return {p["id"]: p for p in firestore_paas.list_products()}

def _pct(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0

THEMES = {"battery": ("battery", "charge", "drain"), "delivery": ("delivery", "deliver", "address", "carrier", "arrived"),
          "packaging": ("packaging", "packed", "box", "cracked"), "sound": ("sound", "earbud", "speaker", "volume", "quiet"),
          "fit and build": ("strap", "loose", "fit", "jar", "clasp"), "value": ("money", "price", "value", "cheap", "saved"),
          "condition": ("condition", "like new", "mark", "scratch", "works")}

def _themes(texts: List[str]) -> List[Dict[str, Any]]:
    counts = collections.Counter()
    for text in texts:
        low = text.lower()
        for theme, words in THEMES.items():
            if any(w in low for w in words):
                counts[theme] += 1
    return [{"theme": t, "mentions": n} for t, n in counts.most_common()]

# ---- PaaS ----
def sales_analytics(tenant, params):
    sales = _sales()
    revenue = round(sum(o["total"] for o in sales), 2)
    units: Dict[str, Dict[str, Any]] = {}
    for o in sales:
        for line in _lines(o):
            row = units.setdefault(line["product_id"], {"product": line["name"], "units": 0, "revenue_usd": 0.0})
            row["units"] += line["quantity"]
            row["revenue_usd"] = round(row["revenue_usd"] + line["price"] * line["quantity"], 2)
    by_day = collections.Counter()
    for o in sales:
        by_day[o["placed"]] += o["total"]
    return {"orders": len(ops._orders()), "orders_sold": len(sales), "revenue_usd": revenue, "average_order_usd": round(revenue / len(sales), 2) if sales else 0.0,
            "cancelled": sum(1 for o in ops._orders() if o["status"] == "cancelled"),
            "by_status": dict(collections.Counter(o["status"] for o in ops._orders())),
            "top_products": sorted(units.values(), key=lambda r: -r["revenue_usd"])[:5],
            "by_day": [{"date": d, "revenue_usd": round(v, 2)} for d, v in sorted(by_day.items())]}

def behavior_insights(tenant, params):
    orders = [o for o in ops._orders() if o["status"] != "cancelled"]
    per_customer = collections.Counter(o.get("customer_email") for o in orders)
    reasons = collections.Counter(r["reason"] for r in ops._returns())
    return {"customers": len(per_customer), "repeat_customers": sum(1 for n in per_customer.values() if n > 1),
            "repeat_rate_pct": _pct(sum(1 for n in per_customer.values() if n > 1), len(per_customer)),
            "return_rate_pct": _pct(len(ops._returns()), len(orders)),
            "why_customers_return": [{"reason": r, "count": n} for r, n in reasons.most_common()],
            "cancelled_orders": sum(1 for o in ops._orders() if o["status"] == "cancelled")}

def feedback_sentiment(tenant, params):
    reviews = store.rows("reviews", "review_id", newest_first=True)
    spread = collections.Counter(r["rating"] for r in reviews)
    positive = sum(1 for r in reviews if r["rating"] >= 4)
    return {"reviews": len(reviews), "average_rating": round(sum(r["rating"] for r in reviews) / len(reviews), 1) if reviews else None,
            "positive_pct": _pct(positive, len(reviews)), "by_rating": {str(k): spread.get(k, 0) for k in (5, 4, 3, 2, 1)},
            "common_themes": _themes([r["comment"] for r in reviews])}

def segments(tenant, params):
    spend: Dict[str, Dict[str, Any]] = {}
    for o in ops._orders():
        if o["status"] == "cancelled":
            continue
        c = spend.setdefault(o.get("customer_email") or o["customer"], {"customer": o["customer"], "orders": 0, "spent_usd": 0.0})
        c["orders"] += 1
        c["spent_usd"] = round(c["spent_usd"] + o["total"], 2)
    groups = {"Repeat buyers": [c for c in spend.values() if c["orders"] > 1],
              "High value (over $150 spent)": [c for c in spend.values() if c["spent_usd"] > 150],
              "New this month (one order)": [c for c in spend.values() if c["orders"] == 1]}
    return {"segments": [{"segment": name, "customers": len(members), "spent_usd": round(sum(c["spent_usd"] for c in members), 2),
                          "members": [c["customer"] for c in members]} for name, members in groups.items()]}

def order_fraud_flags(tenant, params):
    flags = []
    per_customer = collections.Counter(o.get("customer_email") for o in ops._orders())
    for o in ops._orders():
        reasons = []
        if o["total"] >= 300:
            reasons.append("High-value order (over $300)")
        if per_customer[o.get("customer_email")] >= 3:
            reasons.append("Three or more orders from one customer")
        if o["status"] == "cancelled" and o["total"] >= 100:
            reasons.append("A large order cancelled")
        if reasons:
            flags.append({"order_id": o["order_id"], "customer": o["customer"], "total_usd": o["total"], "status": o["status"], "reasons": reasons, "score": min(100, 35 * len(reasons) + 20)})
    return {"flagged": sorted(flags, key=lambda f: -f["score"]), "rules": ["Order total of $300 or more", "Three or more orders from one customer", "A cancelled order of $100 or more"]}

def paas_impact(tenant, params):
    products = _by_product()
    co2, units = 0.0, 0
    for o in _sales():
        for line in _lines(o):
            units += line["quantity"]
            co2 += products.get(line["product_id"], {}).get("carbon_footprint_kg", 0) * line["quantity"]
    return {"items_resold": units, "co2_saved_kg": round(co2, 1), "basis": "Carbon saved by buying each item refurbished instead of new, as recorded on the product"}

# ---- TaaS ----
def delivery_analytics(tenant, params):
    shipments = firestore_taas.list_shipments()
    done = [s for s in shipments if s["status"] == "delivered"]
    judged = [s for s in done if s.get("on_time") is not None]
    days = []
    for s in done:
        if s.get("placed") and s.get("delivered"):
            days.append((datetime.date.fromisoformat(s["delivered"]) - datetime.date.fromisoformat(s["placed"])).days)
    return {"shipments": len(shipments), "delivered": len(done), "in_transit": sum(1 for s in shipments if s["status"] == "in_transit"),
            "on_time_pct": _pct(sum(1 for s in judged if s["on_time"]), len(judged)) if judged else None,
            "avg_days": round(sum(days) / len(days), 1) if days else None, "rules": ops.delivery_rules(), "service_area": ops.service_area(),
            "by_carrier": [{"carrier": c, "shipments": n} for c, n in collections.Counter(s.get("carrier", "") for s in shipments).most_common()]}

def delivery_insights(tenant, params):
    shipments = firestore_taas.list_shipments()
    done = [s for s in shipments if s["status"] == "delivered" and s.get("on_time") is not None]
    patterns = []
    for carrier in sorted({s.get("carrier") for s in done}):
        mine = [s for s in done if s.get("carrier") == carrier]
        rate = _pct(sum(1 for s in mine if s["on_time"]), len(mine))
        patterns.append({"title": f"{carrier}: {rate}% on time", "detail": f"{sum(1 for s in mine if s['on_time'])} of {len(mine)} delivered shipments arrived on time.",
                         "tone": "green" if rate >= 90 else "yellow" if rate >= 70 else "red"})
    electric = [s for s in shipments if s.get("electric")]
    if shipments:
        patterns.append({"title": f"{_pct(len(electric), len(shipments))}% of deliveries are electric", "detail": f"{len(electric)} of {len(shipments)} shipments used an electric vehicle.", "tone": "green"})
    late = [s for s in done if not s["on_time"]]
    if late:
        patterns.append({"title": f"{len(late)} late deliver{'y' if len(late) == 1 else 'ies'}", "detail": "Late: " + ", ".join(s["destination"] for s in late), "tone": "red"})
    return {"patterns": patterns}

def transport_impact(tenant, params):
    shipments = [s for s in firestore_taas.list_shipments() if s["status"] != "cancelled"]
    return {"co2_saved_kg": round(sum(s.get("co2_saved_kg", 0) for s in shipments), 1), "deliveries": len(shipments),
            "electric_share_pct": _pct(sum(1 for s in shipments if s.get("electric")), len(shipments)) if shipments else None,
            "returns_recovered": sum(1 for r in ops._returns() if r.get("route"))}

# ---- SaaS ----
def support_analytics(tenant, params):
    tickets = ops._tickets()
    replied = [t for t in tickets if any(m["from"] == "Staff" for m in t["messages"])]
    return {"tickets": len(tickets), "by_status": dict(collections.Counter(t["status"] for t in tickets)),
            "answered_pct": _pct(len(replied), len(tickets)), "open": sum(1 for t in tickets if t["status"] in ("open", "in_progress")),
            "returns": {"total": len(ops._returns()), "by_status": dict(collections.Counter(r["status"] for r in ops._returns()))},
            "refunded_usd": round(sum(r.get("refunded", 0) for r in ops._returns()), 2)}

def ticket_sentiment(tenant, params):
    tickets = ops._tickets()
    texts = [t["subject"] + " " + " ".join(m["text"] for m in t["messages"] if m["from"] == "Customer") for t in tickets]
    return {"tickets": len(tickets), "common_issues": _themes(texts), "still_open": [t["subject"] for t in tickets if t["status"] in ("open", "in_progress")]}

def consumer_scorecard(tenant, params):
    returns = ops._returns()
    routed = collections.Counter(r["route"] for r in returns if r.get("route"))
    recovered = round(sum(r["amount"] for r in returns if r.get("route") in ("resale", "refurbish")), 2)
    return {"returns": len(returns), "kept_in_use": routed.get("resale", 0) + routed.get("refurbish", 0), "recycled": routed.get("recycle", 0),
            "by_route": dict(routed), "value_recovered_usd": recovered,
            "circularity_pct": _pct(sum(routed.values()), len(returns))}

def return_fraud_flags(tenant, params):
    per_customer = collections.Counter(r["customer"] for r in ops._returns())
    flags = []
    for r in ops._returns():
        reasons = []
        if r["amount"] >= 150 and r["status"] == "requested":
            reasons.append("High-value return waiting for a decision")
        if per_customer[r["customer"]] >= 2:
            reasons.append("The same customer has returned more than one item")
        if reasons:
            flags.append({"return_id": r["return_id"], "customer": r["customer"], "item": r["item"], "amount_usd": r["amount"], "reasons": reasons})
    return {"flagged": flags}

def support_impact(tenant, params):
    routed = [r for r in ops._returns() if r.get("route")]
    products = {p["name"]: p for p in firestore_paas.list_products()}
    co2 = sum(products.get(r["item"], {}).get("carbon_footprint_kg", 0) for r in routed if r["route"] in ("resale", "refurbish"))
    return {"items_kept_out_of_landfill": len(routed), "co2_saved_kg": round(co2, 1), "by_route": dict(collections.Counter(r["route"] for r in routed))}

# ---- MaaS: impact ledger and reports ----
def _ledger() -> List[Dict[str, Any]]:
    entries = []
    for s in firestore_taas.list_shipments():
        if s.get("co2_saved_kg"):
            entries.append({"source": "TaaS", "event": f"Delivery by {s.get('mode', 'vehicle')}", "co2_saved_kg": s["co2_saved_kg"], "date": (s.get("delivered") or s.get("placed") or "")})
    products = {p["name"]: p for p in firestore_paas.list_products()}
    for r in ops._returns():
        if r.get("route") in ("resale", "refurbish"):
            entries.append({"source": "SaaS", "event": f"{r['item']} kept in use ({r['route']})", "co2_saved_kg": products.get(r["item"], {}).get("carbon_footprint_kg", 0), "date": ""})
    for o in _sales():
        for line in _lines(o):
            entries.append({"source": "PaaS", "event": f"{line['name']} sold refurbished", "co2_saved_kg": round(_by_product().get(line["product_id"], {}).get("carbon_footprint_kg", 0) * line["quantity"], 1), "date": o["placed"]})
    from cloud_run import impact  # savings recorded in kg CO2e (green routes, recorded events) join the ledger
    names = {"paas": "PaaS", "taas": "TaaS", "saas": "SaaS"}
    for r in impact.records(store.session().tenant):
        if r["kind"] == "event" and r["unit"].lower() in ("kg co2e", "kg") and r["service"] in names:
            entries.append({"source": names[r["service"]], "event": r["subject"], "co2_saved_kg": r["value"], "date": r["at"][:10]})
    return entries

def impact_ledger(tenant, params):
    entries = _ledger()
    return {"entries": entries, "total_co2_saved_kg": round(sum(e["co2_saved_kg"] for e in entries), 1),
            "by_service": {s: round(sum(e["co2_saved_kg"] for e in entries if e["source"] == s), 1) for s in ("PaaS", "TaaS", "SaaS")}}

def impact_baseline(tenant, params):
    shipments = firestore_taas.list_shipments()
    return {"method": "Without Lakshmi: every item is bought new, every delivery is a conventional diesel delivery and every return is discarded",
            "assumptions": {"diesel_delivery_kg_co2e": BASELINE_KG_PER_DELIVERY}, "deliveries_compared": len(shipments),
            "baseline_delivery_co2_kg": round(len(shipments) * BASELINE_KG_PER_DELIVERY, 1)}

def net_impact(tenant, params):
    ledger = _ledger()
    shipments = firestore_taas.list_shipments()
    actual = round(sum(s.get("co2_kg", 0) for s in shipments), 1)
    return {"co2_saved_kg": round(sum(e["co2_saved_kg"] for e in ledger), 1), "delivery_co2_actual_kg": actual,
            "delivery_co2_baseline_kg": round(len(shipments) * BASELINE_KG_PER_DELIVERY, 1),
            "note": "Figures are estimates against the baseline method, not measurements"}

def ai_footprint(tenant, params):
    ai_paths = {e["path"] for e in endpoint_registry.list_endpoints() if e["ai"]}
    counts = endpoint_registry.call_counts(tenant["tenant_id"], 30)
    calls = sum(n for p, n in counts.items() if p in ai_paths)
    return {"ai_requests_30d": calls, "energy_wh": round(calls * AI_WH_PER_REQUEST, 1), "assumption": f"{AI_WH_PER_REQUEST} Wh per AI request (an estimate)"}

def endpoint_versions(tenant, params):
    on = endpoint_registry.enabled_paths(tenant["tenant_id"])
    by_version = collections.Counter(e["version"] for e in endpoint_registry.list_endpoints() if e["path"] in on)
    return {"versions": [{"version": v, "endpoints": n} for v, n in sorted(by_version.items())]}

def owner_tickets(tenant, params):
    return {"tickets": [t for t in store.rows("platform_tickets", "ticket_id", scope="global", newest_first=True) if t.get("tenant_id") == tenant["tenant_id"]]}

HANDLERS_FOR: Dict[str, Callable] = {
    "/paas/analytics/sales/read/v1": sales_analytics, "/paas/insights/behavior/read/v1": behavior_insights,
    "/paas/insights/feedback/sentiment/read/v1": feedback_sentiment, "/paas/segment/read/v1": segments,
    "/paas/fraud/order/flag/read/v1": order_fraud_flags, "/paas/impact/report/read/v1": paas_impact,
    "/taas/analytics/delivery/read/v1": delivery_analytics, "/taas/insights/delivery/read/v1": delivery_insights, "/taas/impact/report/read/v1": transport_impact,
    "/saas/analytics/support/read/v1": support_analytics, "/saas/insights/ticket-sentiment/read/v1": ticket_sentiment,
    "/saas/scorecard/consumer/read/v1": consumer_scorecard, "/saas/fraud/return/flag/read/v1": return_fraud_flags, "/saas/impact/report/read/v1": support_impact,
    "/maas/impact/ledger/read/v1": impact_ledger, "/maas/impact/baseline/read/v1": impact_baseline, "/maas/impact/report/net/read/v1": net_impact,
    "/maas/impact/ai-footprint/read/v1": ai_footprint, "/maas/endpoint-version/read/v1": endpoint_versions, "/maas/owner-ticket/read/v1": owner_tickets,
}

def install(handlers: Dict[str, Callable]) -> int:
    """Registers these as the real handlers (they win over the preview stand-ins)."""
    handlers.update(HANDLERS_FOR)
    return len(HANDLERS_FOR)
