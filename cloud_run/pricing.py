"""
Cloud Run - dynamic pricing
Suggests a price for one product from the consumer's own records, and applies it when staff accept it.

How a suggestion is worked out (all figures come from the consumer's own data, nothing is typed in):
  demand        sell-through over the last 30 days (units sold / units sold + units in stock)
  stock         days of cover left at the recent selling rate
  condition     refurbished and used goods sit a little below new ones
  bid_pressure  the prices shoppers actually agreed in bids: deals closing near list price mean room to rise, deals
                closing near the floor mean the price is too high (needs at least 2 agreed deals)
Each factor gives a percentage nudge. The nudges are added, then kept inside the consumer's rules:
  max_change_pct   the price never moves further than this from the product's BASE price (the list price before any
                   dynamic change; kept on the product so applying twice never drifts further)
  min_margin_pct   the price never falls below the product's bidding floor plus this margin (the floor is the lowest
                   price the seller accepts, so it stands in for cost)
Nothing here calls an outside service: the same records always give the same suggestion.
"""

import datetime
from typing import Any, Callable, Dict, List, Optional

from firestore import store
from firestore.users.consumer import operations as ops
from cloud_run.ids import new_id

DEFAULT_RULES = {"min_margin_pct": 5.0, "max_change_pct": 15.0, "factors": ["demand", "stock", "condition", "bid_pressure"]}
ALL_FACTORS = ("demand", "stock", "condition", "bid_pressure")
SOLD = ("paid", "shipped", "delivered")
WINDOW_DAYS = 30
NO_CHANGE_PCT = 0.5   # a move smaller than this is not worth a suggestion


def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


# ---------- rules ----------
def get_rules(tenant_id: str) -> Dict[str, Any]:
    doc = store.kdoc("pricing_rules", "current", lambda: dict(DEFAULT_RULES), tenant_id=tenant_id)
    return {"min_margin_pct": float(doc.get("min_margin_pct", DEFAULT_RULES["min_margin_pct"])),
            "max_change_pct": float(doc.get("max_change_pct", DEFAULT_RULES["max_change_pct"])),
            "factors": list(doc.get("factors") or DEFAULT_RULES["factors"])}


def set_rules(tenant_id: str, min_margin_pct: Any, max_change_pct: Any, factors: Optional[List[str]]) -> Dict[str, Any]:
    margin, change = float(min_margin_pct), float(max_change_pct)
    if not 0 <= margin <= 100:
        raise ValueError("The minimum margin must be between 0 and 100 percent.")
    if not 0 < change <= 50:
        raise ValueError("The largest price change must be above 0 and at most 50 percent.")
    chosen = list(dict.fromkeys(str(f).strip() for f in (factors or ALL_FACTORS)))
    unknown = [f for f in chosen if f not in ALL_FACTORS]
    if unknown:
        raise ValueError(f"Unknown factor {', '.join(unknown)}. Use: {', '.join(ALL_FACTORS)}.")
    if not chosen:
        raise ValueError("Pick at least one factor.")
    doc = store.kdoc("pricing_rules", "current", lambda: dict(DEFAULT_RULES), tenant_id=tenant_id)
    doc.clear()
    doc.update({"min_margin_pct": margin, "max_change_pct": change, "factors": chosen, "updated_at": _now(), "updated_by": ops.ACTOR.get() or ""})
    return get_rules(tenant_id)


# ---------- signals ----------
def _recent_units(product_id: str) -> int:
    cutoff = (datetime.date.today() - datetime.timedelta(days=WINDOW_DAYS)).isoformat()
    units = 0
    for order in ops.read_orders(None):
        if order.get("status") not in SOLD or str(order.get("placed", ""))[:10] < cutoff:
            continue
        units += sum(int(l.get("quantity") or 0) for l in order.get("lines") or [] if l.get("product_id") == product_id)
    return units


def _agreed_deals(tenant_id: str, product_id: str) -> List[float]:
    """Prices shoppers agreed in bids on this product, read through the consumer's bid index."""
    index = store.kdoc("bid_index", "all", lambda: {"bids": {}}, tenant_id=tenant_id)["bids"]
    prices = []
    for email in dict.fromkeys(index.values()):
        shopper = store.kdoc("shoppers", email, dict, tenant_id=tenant_id)
        for bid in shopper.get("bids", []):
            if bid.get("product_id") == product_id and bid.get("agreed_price"):
                prices.append(float(bid["agreed_price"]))
    return prices


def factors_for(product: Dict[str, Any], units: int, deals: List[float], enabled: List[str]) -> List[Dict[str, Any]]:
    """The nudges, each in percent of the base price, with the reason in plain words."""
    stock = int(product.get("stock") or 0)
    out: List[Dict[str, Any]] = []
    if "demand" in enabled:
        sell_through = units / (units + stock) if (units + stock) else 0.0
        adj = round(_clamp((sell_through - 0.25) * 40, -8, 8), 2)
        out.append({"factor": "demand", "adjustment_pct": adj,
                    "reason": f"{units} sold in the last {WINDOW_DAYS} days against {stock} in stock ({sell_through:.0%} sell-through; 25% is neutral)."})
    if "stock" in enabled:
        rate = units / WINDOW_DAYS
        cover = stock / rate if rate > 0 else None
        if cover is None:
            adj, why = (-3.0, f"{stock} in stock and none sold recently.") if stock else (0.0, "Out of stock.")
        elif cover > 120:
            adj, why = -6.0, f"About {cover:.0f} days of stock at the current rate: more than 120 days."
        elif cover > 60:
            adj, why = -3.0, f"About {cover:.0f} days of stock at the current rate: more than 60 days."
        elif cover < 14:
            adj, why = 5.0, f"About {cover:.0f} days of stock at the current rate: under 14 days."
        elif cover < 30:
            adj, why = 2.0, f"About {cover:.0f} days of stock at the current rate: under 30 days."
        else:
            adj, why = 0.0, f"About {cover:.0f} days of stock at the current rate: a healthy level."
        out.append({"factor": "stock", "adjustment_pct": adj, "reason": why})
    if "condition" in enabled:
        key = ops.condition_key(product.get("condition", "")) or "new"
        adj = {"new": 0.0, "refurbished": -1.0, "used": -2.0}[key]
        out.append({"factor": "condition", "adjustment_pct": adj, "reason": f"Condition is {key}."})
    if "bid_pressure" in enabled:
        base = float(product.get("base_price") or product["retail_price"])
        if len(deals) >= 2:
            ratio = (sum(deals) / len(deals)) / base
            adj = round(_clamp((ratio - 0.85) * 40, -5, 5), 2)
            out.append({"factor": "bid_pressure", "adjustment_pct": adj,
                        "reason": f"{len(deals)} bids closed at {ratio:.0%} of the list price on average (85% is neutral)."})
        else:
            out.append({"factor": "bid_pressure", "adjustment_pct": 0.0, "reason": "Fewer than 2 agreed bids, so bids say nothing yet."})
    return out


def compute(product: Dict[str, Any], units: int, deals: List[float], rules: Dict[str, Any]) -> Dict[str, Any]:
    """The suggestion for one product. Pure: the same inputs always give the same answer."""
    current = round(float(product["retail_price"]), 2)
    base = round(float(product.get("base_price") or current), 2)
    parts = factors_for(product, units, deals, rules["factors"])
    raw = round(sum(f["adjustment_pct"] for f in parts), 2)
    adj = _clamp(raw, -rules["max_change_pct"], rules["max_change_pct"])
    guardrails = []
    if adj != raw:
        guardrails.append(f"The combined nudge of {raw:+.2f}% was held to the largest change you allow ({rules['max_change_pct']:g}%).")
    target = base * (1 + adj / 100)
    floor = float(product.get("current_bidding_floor") or base * 0.5)
    lowest = round(floor * (1 + rules["min_margin_pct"] / 100), 2)
    if target < lowest:
        guardrails.append(f"The price was held at ${lowest:.2f}, the bidding floor plus the {rules['min_margin_pct']:g}% minimum margin.")
        target = lowest
    suggested = round(target, 2)
    change = round((suggested - current) / current * 100, 2) if current else 0.0
    return {"product_id": product["id"], "name": product["name"], "current_price": current, "base_price": base,
            "suggested_price": suggested, "change_pct": change, "changed": abs(change) >= NO_CHANGE_PCT,
            "factors": parts, "guardrails": guardrails, "lowest_allowed_price": lowest, "rules": rules}


# ---------- handlers ----------
def _product(product_id: str) -> Dict[str, Any]:
    product = next((p for p in ops.list_products() if p["id"] == product_id or p.get("sku") == product_id), None)
    if product is None:
        raise LookupError(f"No product {product_id}")
    return product


def _log(tenant_id: str) -> List[Dict[str, Any]]:
    return store.kdoc("price_suggestions", "all", lambda: {"items": []}, tenant_id=tenant_id)["items"]


def rules_set(tenant, params):
    rules = set_rules(tenant["tenant_id"], params["min_margin_pct"], params["max_change_pct"], params.get("factors"))
    return {"status": "saved", "rules": rules}


def suggest(tenant, params):
    tid = tenant["tenant_id"]
    product = _product(params["product_id"])
    if int(product.get("stock") or 0) <= 0:
        raise ValueError(f"{product['name']} is out of stock, so there is no price to suggest.")
    rules = get_rules(tid)
    result = compute(product, _recent_units(product["id"]), _agreed_deals(tid, product["id"]), rules)
    record = {"suggestion_id": new_id(), **result, "status": "pending" if result["changed"] else "no_change", "at": _now(), "by": ops.ACTOR.get() or "AI"}
    items = _log(tid)
    for older in items:  # a newer suggestion replaces an older pending one for the same product
        if older["product_id"] == record["product_id"] and older["status"] == "pending":
            older["status"] = "superseded"
    items.insert(0, record)
    del items[200:]
    if not result["changed"]:
        record["note"] = "The current price already matches what the signals support. Nothing to apply."
    return record


def apply(tenant, params):
    tid = tenant["tenant_id"]
    record = next((r for r in _log(tid) if r["suggestion_id"] == params["suggestion_id"]), None)
    if record is None:
        raise LookupError(f"No price suggestion {params['suggestion_id']}")
    if record["status"] != "pending":
        raise ValueError(f"This suggestion is already {record['status'].replace('_', ' ')}, so it cannot be applied.")
    product = _product(record["product_id"])
    if round(float(product["retail_price"]), 2) != record["current_price"]:
        record["status"] = "stale"
        raise ValueError(f"The price of {product['name']} changed to ${float(product['retail_price']):.2f} after this suggestion. Ask for a new one.")
    rules = get_rules(tid)
    floor = float(product.get("current_bidding_floor") or 0)
    if record["suggested_price"] < round(floor * (1 + rules["min_margin_pct"] / 100), 2):
        raise ValueError("The suggested price is now below your minimum margin. Ask for a new suggestion.")
    old = round(float(product["retail_price"]), 2)
    product.setdefault("base_price", record["base_price"])
    ops.update_product({"product_id": product["id"], "price": record["suggested_price"]})
    history = product.setdefault("price_history", [])
    history.append({"at": _now(), "from": old, "to": record["suggested_price"], "by": ops.ACTOR.get() or "", "suggestion_id": record["suggestion_id"]})
    del history[:-20]
    record.update({"status": "applied", "applied_at": _now(), "applied_by": ops.ACTOR.get() or ""})
    return {"status": "applied", "product_id": product["id"], "name": product["name"], "old_price": old,
            "new_price": record["suggested_price"], "base_price": product["base_price"], "suggestion_id": record["suggestion_id"]}


def install(handlers: Dict[str, Callable]) -> int:
    table = {"/paas/pricing/dynamic/rules/set/v1": rules_set, "/paas/pricing/dynamic/suggest/v1": suggest, "/paas/pricing/dynamic/apply/v1": apply}
    handlers.update(table)
    return len(table)
