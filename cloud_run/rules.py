"""
Cloud Run - the consumer's rules and settings
What the Root sets on the settings screens, kept per consumer, and read by the features they govern:

  bid rules          ai-limits (lowest price and deepest discount the AI bot may agree, and how many counters it makes),
                     price-limits (the range of opening offers a shopper may make, overall or per category), window (how many
                     hours a bid stays open), seller-eligibility (the lowest seller rating and stock a multi-seller room needs)
  language, region   the languages shoppers may choose, local or global operation, the currencies
  return policy      the return window and refund method for each region
  green credits      credits earned per dollar spent and the dollar value of one credit
  personalization    which of a shopper's activity signals the recommendations may use, and for how many days

A setting nobody has set falls back to the default named next to its getter below. The getters take a consumer's id so any
handler can read them. Nothing here calls an outside service.
"""

import datetime
from typing import Any, Dict, List, Optional

from firestore import store
from firestore.users.consumer import operations as ops
from vertex_ai import gemini

DEFAULT_AI_ROUNDS = 5
DEFAULT_EARN_PER_DOLLAR = 0.1   # one credit for every $10 spent, as before the rule existed
DEFAULT_CREDIT_VALUE = 0.1      # one credit is worth $0.10
SIGNALS = ("cart", "wishlist", "orders", "bids")


def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _doc(tenant_id: str, name: str) -> Dict[str, Any]:
    return store.kdoc(name, "current", dict, tenant_id=tenant_id)


def _put(doc: Dict[str, Any], values: Dict[str, Any]) -> None:
    doc.clear()
    doc.update({**values, "updated_at": _now(), "updated_by": ops.ACTOR.get() or ""})


def _number(value: Any, what: str, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{what} must be a number.")
    if not low <= number <= high:
        raise ValueError(f"{what} must be between {low:g} and {high:g}.")
    return number


# ---------- bid rules ----------
def ai_limits_set(tenant, params):
    doc = _doc(tenant["tenant_id"], "bid_ai_limits")
    _put(doc, {"min_price": _number(params["min_price"], "The lowest price", 0, 1e7),
               "max_discount_pct": _number(params["max_discount_pct"], "The deepest discount", 0, 90),
               "max_rounds": int(_number(params.get("max_rounds") or DEFAULT_AI_ROUNDS, "The number of counters", 1, 10))})
    return {"status": "saved", "ai_limits": ai_limits(tenant["tenant_id"])}


def ai_limits(tenant_id: str) -> Dict[str, Any]:
    d = _doc(tenant_id, "bid_ai_limits")
    return {"min_price": d.get("min_price"), "max_discount_pct": d.get("max_discount_pct"), "max_rounds": int(d.get("max_rounds") or DEFAULT_AI_ROUNDS)}


def effective_floor(tenant_id: str, product: Dict[str, Any]) -> float:
    """The lowest price the bot may agree for a product: its bidding floor, raised by the AI limits."""
    floor, limits = float(product["current_bidding_floor"]), ai_limits(tenant_id)
    if limits["min_price"]:
        floor = max(floor, float(limits["min_price"]))
    if limits["max_discount_pct"] is not None:
        floor = max(floor, float(product["retail_price"]) * (1 - float(limits["max_discount_pct"]) / 100))
    return round(floor, 2)


def price_limits_set(tenant, params):
    floor = _number(params["floor"], "The floor", 0, 1e7)
    ceiling = _number(params["ceiling"], "The ceiling", 0, 1e7)
    if ceiling <= floor:
        raise ValueError("The ceiling must be above the floor.")
    doc = _doc(tenant["tenant_id"], "bid_price_limits")
    limits = dict(doc.get("limits") or {})
    limits[str(params.get("category_id") or "*")] = {"floor": floor, "ceiling": ceiling}
    _put(doc, {"limits": limits})
    return {"status": "saved", "price_limits": limits}


def check_offer(tenant_id: str, product: Dict[str, Any], offer: float) -> None:
    """Refuses an opening offer outside the range set for the product's category (or the overall range)."""
    limits = _doc(tenant_id, "bid_price_limits").get("limits") or {}
    rule = limits.get(str(product.get("category"))) or limits.get("*")
    if not rule:
        return
    if offer < rule["floor"]:
        raise ValueError(f"Offers below ${rule['floor']:.2f} are not accepted for this product.")
    if offer > rule["ceiling"]:
        raise ValueError(f"Offers above ${rule['ceiling']:.2f} are not needed: please buy it at its price instead.")


def window_set(tenant, params):
    hours = int(_number(params["duration_hours"], "The window", 1, 720))
    _put(_doc(tenant["tenant_id"], "bid_window"), {"duration_hours": hours})
    return {"status": "saved", "duration_hours": hours}


def window_hours(tenant_id: str) -> Optional[int]:
    return _doc(tenant_id, "bid_window").get("duration_hours")


def expired(tenant_id: str, bid: Dict[str, Any]) -> bool:
    hours = window_hours(tenant_id)
    if not hours:
        return False
    try:
        opened = datetime.datetime.strptime(bid["at"], "%Y-%m-%d %H:%M")
    except (KeyError, ValueError):
        return False
    return datetime.datetime.utcnow() - opened > datetime.timedelta(hours=hours)


def eligibility_set(tenant, params):
    regions = [str(r).strip() for r in (params.get("regions") or []) if str(r).strip()]
    _put(_doc(tenant["tenant_id"], "bid_eligibility"),
         {"min_rating": _number(params.get("min_rating") or 0, "The rating", 0, 5), "min_stock": int(_number(params.get("min_stock") or 0, "The stock", 0, 1e6)), "regions": regions})
    return {"status": "saved", "seller_eligibility": eligibility(tenant["tenant_id"])}


def eligibility(tenant_id: str) -> Dict[str, Any]:
    d = _doc(tenant_id, "bid_eligibility")
    return {"min_rating": float(d.get("min_rating") or 0), "min_stock": int(d.get("min_stock") or 0), "regions": list(d.get("regions") or [])}


# ---------- language, region, currency ----------
def language_set(tenant, params):
    languages = list(dict.fromkeys(str(l).strip().lower() for l in params["languages"] if str(l).strip()))
    unknown = [l for l in languages if l not in gemini.LANGUAGE_NAMES]
    if not languages or unknown:
        raise ValueError("Pick from: " + ", ".join(f"{n} ({c})" for c, n in gemini.LANGUAGE_NAMES.items()) + (f". Not supported: {', '.join(unknown)}." if unknown else "."))
    default = str(params["default_language"]).strip().lower()
    if default not in languages:
        raise ValueError("The default language must be one of the languages you picked.")
    doc = _doc(tenant["tenant_id"], "locale")
    _put(doc, {**{k: v for k, v in doc.items() if k not in ("updated_at", "updated_by")}, "languages": languages, "default_language": default})
    return {"status": "saved", "locale": locale(tenant["tenant_id"])}


def region_set(tenant, params):
    mode = params["mode"]
    regions = [str(r).strip() for r in (params.get("regions") or []) if str(r).strip()]
    if mode == "local" and not regions:
        raise ValueError("Name at least one region for local operation.")
    doc = _doc(tenant["tenant_id"], "locale")
    _put(doc, {**{k: v for k, v in doc.items() if k not in ("updated_at", "updated_by")}, "mode": mode, "regions": regions if mode == "local" else []})
    return {"status": "saved", "locale": locale(tenant["tenant_id"])}


def currency_set(tenant, params):
    codes = list(dict.fromkeys(str(c).strip().upper() for c in params["currencies"] if str(c).strip()))
    if not codes or any(len(c) != 3 or not c.isalpha() for c in codes):
        raise ValueError("Give currencies as 3-letter codes, for example INR, USD.")
    default = str(params["default_currency"]).strip().upper()
    if default not in codes:
        raise ValueError("The default currency must be one of the currencies you listed.")
    doc = _doc(tenant["tenant_id"], "locale")
    _put(doc, {**{k: v for k, v in doc.items() if k not in ("updated_at", "updated_by")}, "currencies": codes, "default_currency": default})
    return {"status": "saved", "locale": locale(tenant["tenant_id"])}


def locale(tenant_id: str) -> Dict[str, Any]:
    d = _doc(tenant_id, "locale")
    return {"languages": list(d.get("languages") or []), "default_language": d.get("default_language"), "mode": d.get("mode") or "global",
            "regions": list(d.get("regions") or []), "currencies": list(d.get("currencies") or []), "default_currency": d.get("default_currency")}


def customer_language_ok(tenant_id: str, language: str) -> None:
    """A shopper may only pick a language the consumer offers (any of the nine when it has not chosen)."""
    offered = locale(tenant_id)["languages"]
    if offered and language not in offered:
        raise ValueError("This store offers: " + ", ".join(f"{gemini.LANGUAGE_NAMES.get(l, l)} ({l})" for l in offered) + ".")


def policy_region_set(tenant, params):
    window = int(_number(params["window_days"], "The return window", 0, 365))
    region = str(params["region"]).strip()
    if not region:
        raise ValueError("Name the region.")
    doc = _doc(tenant["tenant_id"], "return_policy_regions")
    regions = dict(doc.get("regions") or {})
    regions[region.lower()] = {"region": region, "window_days": window, "refund_method": params.get("refund_method") or "original"}
    _put(doc, {"regions": regions})
    return {"status": "saved", "region_policy": regions[region.lower()], "regions": sorted(regions)}


# ---------- green credits ----------
def green_rules_set(tenant, params):
    earn = _number(params["earn_per_unit"], "Credits earned per dollar", 0, 10)
    value = _number(params["redeem_value"], "The value of a credit", 0, 10)
    _put(_doc(tenant["tenant_id"], "green_rules"), {"earn_per_unit": earn, "redeem_value": value})
    return {"status": "saved", "green_credits": green_rules(tenant["tenant_id"])}


def green_rules(tenant_id: str) -> Dict[str, Any]:
    d = _doc(tenant_id, "green_rules")
    earn, value = d.get("earn_per_unit"), d.get("redeem_value")
    return {"earn_per_unit": DEFAULT_EARN_PER_DOLLAR if earn is None else float(earn), "redeem_value": DEFAULT_CREDIT_VALUE if value is None else float(value)}


def green_earn(tenant, params):
    email = str(params["customer_id"]).strip().lower()
    amount = int(_number(params["amount"], "The amount", 1, 10000))
    reason = str(params["reason"]).strip()
    if not reason:
        raise ValueError("Give a reason for the credits.")
    shopper = store.kdoc("shoppers", email, dict, tenant_id=tenant["tenant_id"])
    if not shopper.get("profile"):
        raise LookupError(f"No shopper {email}")
    shopper["green_credits"] = int(shopper.get("green_credits") or 0) + amount
    log = shopper.setdefault("credit_log", [])
    log.insert(0, {"amount": amount, "reason": reason[:200], "at": _now(), "by": ops.ACTOR.get() or "System"})
    del log[50:]
    return {"status": "awarded", "customer": email, "awarded": amount, "balance": shopper["green_credits"]}


# ---------- personalization limits ----------
def personalization_set(tenant, params):
    signals = list(dict.fromkeys(str(s).strip().lower() for s in (params.get("enabled_signals") or SIGNALS)))
    unknown = [s for s in signals if s not in SIGNALS]
    if unknown or not signals:
        raise ValueError("Signals can be: " + ", ".join(SIGNALS) + (f". Not known: {', '.join(unknown)}." if unknown else "."))
    days = params.get("retention_days")
    days = int(_number(days, "Retention", 1, 3650)) if days not in (None, "") else None
    _put(_doc(tenant["tenant_id"], "personalization"), {"enabled_signals": signals, "retention_days": days})
    return {"status": "saved", "personalization": personalization(tenant["tenant_id"])}


def personalization(tenant_id: str) -> Dict[str, Any]:
    d = _doc(tenant_id, "personalization")
    return {"enabled_signals": list(d.get("enabled_signals") or SIGNALS), "retention_days": d.get("retention_days")}


def within_retention(tenant_id: str, stamp: Optional[str]) -> bool:
    """True when a record dated `stamp` ("YYYY-MM-DD ..." ) is inside the retention window (always, when none is set)."""
    days = personalization(tenant_id)["retention_days"]
    if not days or not stamp:
        return True
    cutoff = (datetime.date.today() - datetime.timedelta(days=int(days))).isoformat()
    return str(stamp)[:10] >= cutoff


def install(handlers) -> int:
    table = {
        "/paas/bid/rules/ai-limits/set/v1": ai_limits_set, "/paas/bid/rules/price-limits/set/v1": price_limits_set,
        "/paas/bid/rules/window/set/v1": window_set, "/paas/bid/rules/seller-eligibility/set/v1": eligibility_set,
        "/maas/locale/language/set/v1": language_set, "/maas/locale/region/set/v1": region_set, "/maas/locale/currency/set/v1": currency_set,
        "/saas/locale/policy/region/set/v1": policy_region_set, "/paas/green-credits/rules/set/v1": green_rules_set,
        "/paas/green-credits/earn/v1": green_earn, "/paas/personalization/limits/set/v1": personalization_set,
    }
    handlers.update(table)
    return len(table)
