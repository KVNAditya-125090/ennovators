"""
Cloud Run - customer segments, offers, bundles and profiles
Personalization worked out from the consumer's own orders and each shopper's own record.

  segment/generate     groups customers by what they bought and spent: repeat buyers, high value, one-order newcomers and
                       customers who have gone quiet. The thresholds can be changed with criteria.
  segment/offer/send   puts an offer (title, optional discount) in every member's record. The shopper's personalized price on
                       a product then reflects it, never going below the seller's bidding floor.
  basket/bundle/suggest  products most often bought with a product (then the same category), priced a few percent under the
                       items bought separately and never under their bidding floors.
  basket/bundle/create staff create a bundle at a price between the floors and the list total.
  profile/build        a shopper's tastes from their cart, wishlist, orders and bids, using only the signals the consumer allows.
  profile/reset        the shopper clears their built profile and wishlist.

Nothing here sends mail or calls an outside service.
"""

import collections
import datetime
import re
from typing import Any, Callable, Dict, List

from firestore import store
from firestore.users.consumer import operations as ops
from cloud_run.ids import new_id
from cloud_run import rules

DEFAULT_CRITERIA = {"high_value_usd": 150.0, "inactive_days": 60, "repeat_orders": 2}
BUNDLE_DISCOUNT = {2: 5.0, 3: 8.0}   # percent off the items bought separately, by bundle size
MAX_BUNDLE_DISCOUNT = 10.0
MAX_OFFER_DISCOUNT = 50.0


def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _shopper(tenant_id: str, email: str) -> Dict[str, Any]:
    doc = store.kdoc("shoppers", email, dict, tenant_id=tenant_id)
    if not doc.get("profile"):
        raise LookupError(f"No shopper {email}")
    return doc


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# ---------- segments ----------
def _customers() -> Dict[str, Dict[str, Any]]:
    people: Dict[str, Dict[str, Any]] = {}
    for o in ops.read_orders(None):
        if o.get("status") == "cancelled" or not o.get("customer_email"):
            continue
        c = people.setdefault(o["customer_email"].lower(), {"email": o["customer_email"].lower(), "customer": o.get("customer") or o["customer_email"], "orders": 0, "spent_usd": 0.0, "last_order": ""})
        c["orders"] += 1
        c["spent_usd"] = round(c["spent_usd"] + float(o.get("total") or 0), 2)
        c["last_order"] = max(c["last_order"], str(o.get("placed", ""))[:10])
    return people


def segment_generate(tenant, params):
    criteria = {**DEFAULT_CRITERIA}
    for key, value in (params.get("criteria") or {}).items():
        if key not in DEFAULT_CRITERIA:
            raise ValueError("Criteria can be: " + ", ".join(DEFAULT_CRITERIA) + f". Not known: {key}.")
        try:
            criteria[key] = float(value) if key == "high_value_usd" else int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{key} must be a number.")
        if criteria[key] <= 0:
            raise ValueError(f"{key} must be above zero.")
    cutoff = (datetime.date.today() - datetime.timedelta(days=criteria["inactive_days"])).isoformat()
    people = list(_customers().values())
    rules_ = [
        (f"Repeat buyers ({criteria['repeat_orders']}+ orders)", lambda c: c["orders"] >= criteria["repeat_orders"]),
        (f"High value (over ${criteria['high_value_usd']:g} spent)", lambda c: c["spent_usd"] > criteria["high_value_usd"]),
        ("New (one order)", lambda c: c["orders"] == 1),
        (f"Gone quiet ({criteria['inactive_days']}+ days without an order)", lambda c: bool(c["last_order"]) and c["last_order"] < cutoff),
    ]
    segments = []
    for name, test in rules_:
        members = [c for c in people if test(c)]
        segments.append({"segment_id": _slug(name.split(" (")[0]), "name": name, "customers": len(members), "spent_usd": round(sum(c["spent_usd"] for c in members), 2), "members": members})
    doc = store.kdoc("segments", "latest", dict, tenant_id=tenant["tenant_id"])
    doc.clear()
    doc.update({"generated_at": _now(), "criteria": criteria, "segments": segments})
    return {"generated_at": doc["generated_at"], "criteria": criteria, "customers_considered": len(people),
            "segments": [{k: v for k, v in s.items() if k != "members"} for s in segments]}


def segment_offer_send(tenant, params):
    tid = tenant["tenant_id"]
    latest = store.kdoc("segments", "latest", dict, tenant_id=tid)
    segment = next((s for s in latest.get("segments", []) if s["segment_id"] == params["segment_id"]), None)
    if segment is None:
        raise LookupError(f"No segment {params['segment_id']}. Generate the segments first, then use one of: " + ", ".join(s["segment_id"] for s in latest.get("segments", [])))
    offer = params["offer"]
    if not isinstance(offer, dict):
        raise ValueError("The offer must be an object such as {\"title\": \"Welcome back\", \"discount_pct\": 10}.")
    title = str(offer.get("title") or "").strip()
    if not title:
        raise ValueError("The offer needs a title.")
    discount = float(offer.get("discount_pct") or 0)
    if not 0 <= discount <= MAX_OFFER_DISCOUNT:
        raise ValueError(f"The discount must be between 0 and {MAX_OFFER_DISCOUNT:g} percent.")
    record = {"offer_id": new_id(), "segment_id": segment["segment_id"], "title": title[:100], "message": str(offer.get("message") or "")[:300],
              "discount_pct": discount, "expires": str(offer.get("expires") or "")[:10], "sent_at": _now(), "sent_by": ops.ACTOR.get() or ""}
    sent = skipped = 0
    for member in segment["members"]:
        doc = store.kdoc("shoppers", member["email"], dict, tenant_id=tid)
        if not doc.get("profile"):
            skipped += 1   # a customer with orders but no shopper account here cannot receive it
            continue
        offers = doc.setdefault("offers", [])
        offers.insert(0, record)
        del offers[10:]
        sent += 1
    ops.send_root_mail(tid, "segment_offer", None, f"Offer '{title}' sent to {sent} customer(s) in {segment['name']}.")
    return {"status": "sent", "offer_id": record["offer_id"], "segment": segment["name"], "sent_to": sent, "skipped": skipped}


# ---------- bundles ----------
def _products() -> Dict[str, Dict[str, Any]]:
    return {p["id"]: p for p in ops.list_products()}


def _round2(x: float) -> float:
    return round(x + 1e-9, 2)


def bundle_suggest(tenant, params):
    by_id = _products()
    anchor = by_id.get(params["product_id"]) or next((p for p in by_id.values() if p.get("sku") == params["product_id"]), None)
    if anchor is None:
        raise LookupError(f"No product {params['product_id']}")
    together: collections.Counter = collections.Counter()
    for o in ops.read_orders(None):
        if o.get("status") == "cancelled":
            continue
        ids = {l["product_id"] for l in o.get("lines") or []}
        if anchor["id"] in ids:
            together.update(i for i in ids if i != anchor["id"])
    candidates = [(i, n, f"bought together {n} time(s)") for i, n in together.most_common() if i in by_id and int(by_id[i].get("stock") or 0) > 0]
    same_category = sorted((p for p in by_id.values() if p["id"] != anchor["id"] and p["id"] not in together and p.get("category") == anchor.get("category") and int(p.get("stock") or 0) > 0),
                           key=lambda p: -float(p.get("carbon_footprint_kg") or 0))
    candidates += [(p["id"], 0, "same category, greener first") for p in same_category]
    picked = candidates[:2]
    if not picked or int(anchor.get("stock") or 0) <= 0:
        raise ValueError("No other in-stock product goes with this one yet.")
    items = [anchor] + [by_id[i] for i, _, _ in picked]
    list_total = sum(float(p["retail_price"]) for p in items)
    discount = min(BUNDLE_DISCOUNT.get(len(items), MAX_BUNDLE_DISCOUNT), MAX_BUNDLE_DISCOUNT)
    lowest = sum(float(p["current_bidding_floor"]) for p in items)
    price = max(_round2(list_total * (1 - discount / 100)), _round2(lowest))   # never below the floors of the items
    return {"product_id": anchor["id"], "products": [{"product_id": p["id"], "name": p["name"], "price": float(p["retail_price"])} for p in items],
            "why": [{"product_id": by_id[i]["id"], "name": by_id[i]["name"], "reason": why} for i, _, why in picked],
            "list_total": _round2(list_total), "bundle_price": price, "saving": _round2(list_total - price), "discount_pct": round((list_total - price) / list_total * 100, 1)}


def bundle_create(tenant, params):
    by_id = _products()
    ids = list(dict.fromkeys(str(i) for i in params["product_ids"]))
    missing = [i for i in ids if i not in by_id]
    if len(ids) < 2:
        raise ValueError("A bundle needs at least 2 different products.")
    if missing:
        raise LookupError("No product " + ", ".join(missing))
    name = str(params["name"]).strip()
    if not name:
        raise ValueError("Give the bundle a name.")
    price = float(params["price"])
    list_total = sum(float(by_id[i]["retail_price"]) for i in ids)
    lowest = sum(float(by_id[i]["current_bidding_floor"]) for i in ids)
    if price <= 0 or price > _round2(list_total):
        raise ValueError(f"The bundle price must be above 0 and at most ${list_total:.2f}, what the items cost separately.")
    if price < _round2(lowest):
        raise ValueError(f"The bundle price cannot be below ${lowest:.2f}, the bidding floors of its items added up.")
    items = store.kdoc("bundles", "all", lambda: {"items": []}, tenant_id=tenant["tenant_id"])["items"]
    bundle = {"bundle_id": new_id(), "name": name[:100], "product_ids": ids, "price": round(price, 2), "list_total": _round2(list_total),
              "saving": _round2(list_total - price), "active": True, "created_at": _now(), "created_by": ops.ACTOR.get() or ""}
    items.insert(0, bundle)
    return bundle


# ---------- profiles ----------
def _profile(tenant_id: str, doc: Dict[str, Any]) -> Dict[str, Any]:
    by_id = _products()
    use = set(rules.personalization(tenant_id)["enabled_signals"])
    fresh = lambda stamp: rules.within_retention(tenant_id, stamp)
    sources: Dict[str, List[str]] = {
        "cart": [l["product_id"] for l in doc.get("cart", [])] if "cart" in use else [],
        "wishlist": [w["product_id"] for w in doc.get("wishlist", [])] if "wishlist" in use else [],
        "orders": [l["product_id"] for o in doc.get("orders", []) if fresh(o.get("placed_at")) for l in o["lines"]] if "orders" in use else [],
        "bids": [b["product_id"] for b in doc.get("bids", []) if fresh(b.get("at"))] if "bids" in use else []}
    interest = [i for ids in sources.values() for i in ids if i in by_id]
    categories = collections.Counter(by_id[i].get("category") for i in interest)
    bought = [by_id[i] for i in sources["orders"] if i in by_id]
    totals = [float(o.get("total_usd") or 0) for o in doc.get("orders", []) if "orders" in use and fresh(o.get("placed_at"))]
    carbon = [float(p.get("carbon_footprint_kg") or 0) for p in bought]
    return {"built_at": _now(), "signals_used": sorted(use), "top_categories": [c for c, _ in categories.most_common(3)],
            "orders": len(totals), "average_order_usd": round(sum(totals) / len(totals), 2) if totals else None,
            "price_band_usd": [min(float(p["retail_price"]) for p in bought), max(float(p["retail_price"]) for p in bought)] if bought else None,
            "average_carbon_saved_kg": round(sum(carbon) / len(carbon), 1) if carbon else None,
            "language": (doc.get("profile") or {}).get("preferred_language", "en"), "bids_made": len(sources["bids"]),
            "segments": [s["name"] for s in store.kdoc("segments", "latest", dict, tenant_id=tenant_id).get("segments", [])
                         if any(m["email"] == (doc["profile"].get("email") or "").lower() for m in s["members"])]}


def profile_build(tenant, params):
    email = str(params["customer_id"]).strip().lower()
    doc = _shopper(tenant["tenant_id"], email)
    doc["profile_data"] = _profile(tenant["tenant_id"], doc)
    return {"customer": email, "profile": doc["profile_data"]}


def profile_reset(tenant, params):
    email = (ops.CUSTOMER.get() or "").strip().lower()
    doc = _shopper(tenant["tenant_id"], email)
    cleared = {"profile": bool(doc.pop("profile_data", None)), "wishlist_items": len(doc.get("wishlist", [])), "offers": len(doc.get("offers", []))}
    doc["wishlist"] = []
    doc["offers"] = []
    return {"status": "reset", "cleared": cleared, "kept": "Your orders, cart, bids and account are untouched."}


def install(handlers: Dict[str, Callable]) -> int:
    table = {"/paas/segment/generate/v1": segment_generate, "/paas/segment/offer/send/v1": segment_offer_send,
             "/paas/basket/bundle/suggest/v1": bundle_suggest, "/paas/basket/bundle/create/v1": bundle_create,
             "/paas/personalization/profile/build/v1": profile_build, "/paas/personalization/profile/reset/v1": profile_reset}
    handlers.update(table)
    return len(table)
