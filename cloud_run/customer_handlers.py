"""
Cloud Run - Customer portal handlers
What a Customer (shopper) call does once it has passed the gate, by catalog path. A shopper has a separate account
with each consumer they shop with, so every shopper's data (profile, cart, wishlist, orders, tickets, reservations,
reviews, green credits) is kept per (consumer, shopper) in this process's memory, like the rest of the preview.

A handler takes the tenant (the consumer whose store this is) and the call's parameters, and returns the response
body. Reads that have real sample data behind them (catalog, passport, environmental scores, stores, tracking)
return it; the AI features answer through Vertex AI; everything else records what was sent and reads back what was
recorded, each answer carrying "preview": true so the interface can say the result is not real yet. Real backend
handlers replace these later - to integrate one, add it to REAL below (a real handler always wins).

Nothing here sends mail, moves money or creates a real session: this is the preview backend for the Customer portal.
"""

import datetime
import itertools
from typing import Any, Callable, Dict, List, Optional

from firestore.services.paas import firestore_paas
from firestore.users.consumer import operations as ops
from vertex_ai.users import customer as vertex_ai
from cloud_storage.users import customer as cloud_storage
from cloud_run.ids import new_id, passport_id, seed_id

# ---- Per-shopper state, kept per (consumer tenant, shopper email) ----
_ids = itertools.count(1)
STATE: Dict[tuple, Dict[str, Any]] = {}      # (tenant_id, email) -> this shopper's data
RECORDS: Dict[tuple, List[Dict[str, Any]]] = {}  # (tenant_id, email, feature) -> stand-in records, newest first

# Demo shopper, so the portal has history on first sign-in (customer@gmail.com, Individual)
DEMO_EMAIL = "customer@gmail.com"


def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _who() -> str:
    """The shopper making this call (their email). The gate sets it for Customer-side endpoints."""
    email = ops.CUSTOMER.get() or DEMO_EMAIL
    return email.strip().lower()


def _state(tenant) -> Dict[str, Any]:
    key = (tenant["tenant_id"], _who())
    if key not in STATE:
        STATE[key] = {
            "profile": {"email": key[1], "account_type": "individual", "full_name": "", "phone": "",
                        "preferred_language": "en", "address": None, "verified": False,
                        "consumer": tenant["name"], "joined": _now()},
            "cart": [], "wishlist": [], "orders": [], "tickets": [], "reservations": [],
            "reviews": [], "green_credits": 120, "bids": [],
        }
    return STATE[key]


def _product(product_id: str) -> Dict[str, Any]:
    product = next((p for p in firestore_paas.list_products() if p["id"] == product_id or p.get("sku") == product_id), None)
    if product is None:
        raise LookupError(f"No product {product_id}")
    return product


def _oid(prefix: str = "") -> str:
    """A new record id: a UUID (the prefix is ignored, kept so callers read the same)."""
    return new_id()


# ---- A plain stand-in, used for every Customer endpoint without a richer handler below ----
def _standin(endpoint: Dict[str, Any]):
    feature = endpoint["feature"]
    is_read = endpoint["method"] == "GET"

    def handler(tenant, params):
        key = (tenant["tenant_id"], _who(), feature)
        if is_read:
            items = [r for r in RECORDS.get(key, [])
                     if all(str(r["params"].get(k)) == str(v) for k, v in params.items() if v not in (None, "") and k in r["params"])]
            return {"preview": True, "items": items,
                    "note": "Preview: shows what you recorded for this feature in this session. Real data arrives once the backend is connected."}
        record = {"id": _oid("pv"), "action": endpoint["sub_category"].replace("/", " "), "endpoint": endpoint["path"],
                  "params": params, "at": _now(), "by": _who(), "status": "recorded"}
        RECORDS.setdefault(key, []).insert(0, record)
        return {"preview": True, "record": record,
                "message": f"{endpoint['description']}: recorded in the preview. It takes effect once the backend is connected."}

    return handler


# ---- Real handlers, by catalog path. A real handler always wins over the stand-in. ----
REAL: Dict[str, Callable[[Any, Dict[str, Any]], Any]] = {}


def real(path: str):
    def register(fn):
        REAL[path] = fn
        return fn
    return register


# ---------- MaaS: account, locale, stores ----------
def _register(tenant, params, account_type):
    st = _state(tenant)
    st["profile"].update({"account_type": account_type,
                          "full_name": params.get("full_name") or params.get("contact_name") or st["profile"]["full_name"],
                          "business_name": params.get("business_name"),
                          "tax_id": params.get("tax_id"),
                          "phone": params.get("phone", st["profile"]["phone"]),
                          "preferred_language": params.get("preferred_language", st["profile"]["preferred_language"])})
    return {"preview": True, "status": "registered", "account_type": account_type, "profile": st["profile"],
            "message": f"Account created with {tenant['name']}. Verify your email to finish."}


@real("/maas/customer-account/register/individual/v1")
def register_individual(tenant, params):
    return _register(tenant, params, "individual")


@real("/maas/customer-account/register/business/v1")
def register_business(tenant, params):
    return _register(tenant, params, "business")


@real("/maas/customer-account/login/v1")
def customer_login(tenant, params):
    st = _state(tenant)
    return {"preview": True, "status": "signed_in", "profile": st["profile"],
            "session": {"access_token": "preview-" + _oid("tok"), "refresh_token": "preview-" + _oid("rtok"), "expires_in": 3600},
            "message": f"Signed in to {tenant['name']} (single sign-on across its enabled services)."}


@real("/maas/customer-account/profile/read/v1")
def read_profile(tenant, params):
    return {"profile": _state(tenant)["profile"]}


@real("/maas/customer-account/profile/update/v1")
def update_profile(tenant, params):
    st = _state(tenant)
    for key in ("full_name", "phone", "preferred_language", "address"):
        if params.get(key) not in (None, ""):
            st["profile"][key] = params[key]
    return {"status": "updated", "profile": st["profile"]}


@real("/maas/customer-account/logout/v1")
def customer_logout(tenant, params):
    return {"status": "signed_out", "message": "Signed out of this device."}


@real("/maas/customer-account/session/refresh/v1")
def refresh_session(tenant, params):
    return {"status": "refreshed", "session": {"access_token": "preview-" + _oid("tok"), "expires_in": 3600}}


@real("/maas/customer-account/mail/verify/v1")
def verify_mail(tenant, params):
    _state(tenant)["profile"]["verified"] = True
    return {"status": "verified", "message": "Email verified."}


@real("/maas/locale/language/customer-select/v1")
def select_language(tenant, params):
    _state(tenant)["profile"]["preferred_language"] = params["language"]
    return {"status": "ok", "preferred_language": params["language"]}


@real("/maas/customer-account/data/export/v1")
def export_data(tenant, params):
    st = _state(tenant)
    return {"format": params.get("format", "json"), "generated_at": _now(), "data": st,
            "message": "Your data, ready to download."}


_STORES = [
    {"store_id": "b44f7827-a2af-58f3-95c1-93a5f83550c1", "name": "Lakshmi Pune", "address": "27 Baner Road, Pune 411045", "city": "Pune", "country": "India", "latitude": 18.559, "longitude": 73.780, "opening_hours": "Mon-Sat 10:00-19:00"},
    {"store_id": "dd52a7c6-9a95-5fea-8b76-6e443d84a6f6", "name": "Lakshmi Mumbai", "address": "14 Linking Road, Bandra, Mumbai 400050", "city": "Mumbai", "country": "India", "latitude": 19.054, "longitude": 72.840, "opening_hours": "Mon-Sun 11:00-20:00"},
    {"store_id": "869a4bcf-360c-5423-8523-a84863e21d81", "name": "Lakshmi Hyderabad", "address": "8 Jubilee Hills, Hyderabad 500033", "city": "Hyderabad", "country": "India", "latitude": 17.431, "longitude": 78.409, "opening_hours": "Mon-Sat 10:30-19:30"},
]


@real("/maas/location/store/list/v1")
def list_stores(tenant, params):
    return {"stores": _STORES}


@real("/maas/location/store/nearby/find/v1")
def nearby_store(tenant, params):
    lat, lng = float(params["latitude"]), float(params["longitude"])
    nearest = min(_STORES, key=lambda s: (s["latitude"] - lat) ** 2 + (s["longitude"] - lng) ** 2)
    km = round((((nearest["latitude"] - lat) ** 2 + (nearest["longitude"] - lng) ** 2) ** 0.5) * 111, 1)
    return {"nearest": {**nearest, "distance_km": km}, "stores": _STORES}


@real("/maas/assistant/account-help/ask/v1")
def account_help(tenant, params):
    return {"preview": True, **vertex_ai.chat(params["question"], {"topic": "account and login"})}


# ---------- PaaS: catalog ----------
def _offer(product: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": product["id"], "name": product["name"], "sku": product.get("sku"), "category": product.get("category"),
            "price": product.get("retail_price"), "bidding_floor": product.get("current_bidding_floor"),
            "condition": product.get("condition"), "stock": product.get("stock"), "image_url": product.get("image_url"),
            "carbon_footprint_kg": product.get("carbon_footprint_kg")}


@real("/paas/catalog/product/view/v1")
def view_product(tenant, params):
    p = _product(params["product_id"])
    return {"product": {**_offer(p), "rating": 4.8, "reviews": len(_state(tenant)["reviews"]),
                        "passport_id": passport_id(p["id"]), "seller": tenant["name"]}}


@real("/paas/catalog/search/text/v1")
def search_text(tenant, params):
    q = str(params["query"]).lower()
    hits = [_offer(p) for p in firestore_paas.list_products() if q in p["name"].lower() or q in p.get("category", "").lower()]
    return {"query": params["query"], "results": hits, "count": len(hits)}


@real("/paas/store-stock/read/v1")
def store_stock(tenant, params):
    p = _product(params["product_id"])
    base = p.get("stock", 0)
    return {"product_id": p["id"], "name": p["name"],
            "by_store": [{"store_id": s["store_id"], "store": s["name"], "in_stock": max(0, base // (i + 1))} for i, s in enumerate(_STORES)]}


@real("/paas/passport/read/v1")
def read_passport(tenant, params):
    pid = params.get("passport_id", "")
    return {"passport": {"passport_id": pid, "origin": "Assembled in Pune, India from 62% recycled aluminium",
                         "owners": 2, "repairs": [{"at": "2026-05-12", "note": "Battery replaced, certified"}],
                         "grades": [{"at": "2026-05-12", "grade": "A", "note": "Refurbished to as-new"}],
                         "carbon_saved_kg": 4.2, "recyclable_pct": 86}}


@real("/paas/passport/scan/v1")
def scan_passport(tenant, params):
    return read_passport(tenant, {"passport_id": params.get("qr_code", "")})


@real("/paas/recommendation/product/read/v1")
def recommend_products(tenant, params):
    st = _state(tenant)
    products = firestore_paas.list_products()
    by_id = {p["id"]: p for p in products}
    seen = {l["product_id"] for l in st["cart"]} | {w["product_id"] for w in st["wishlist"]} \
        | {l["product_id"] for o in st["orders"] for l in o["lines"]} | {b["product_id"] for b in st["bids"]}
    if params.get("product_id"):
        seen.add(params["product_id"])
    liked = {by_id[i].get("category") for i in seen if i in by_id}
    # what the shopper has not met yet, in the categories they have shown interest in first, then the greenest
    pool = [p for p in products if p["id"] not in seen]
    pool.sort(key=lambda p: (p.get("category") not in liked, -p.get("carbon_footprint_kg", 0)))
    items = [_offer(p) for p in pool[: int(params.get("limit") or 3)]]
    reason = "Picked from what you have in your cart, wishlist, orders and bids." if seen else "Popular with shoppers, greenest first. It sharpens as you browse and buy."
    return {"recommendations": items, "reason": reason}


@real("/paas/recommendation/sustainable/read/v1")
def recommend_sustainable(tenant, params):
    items = sorted(firestore_paas.list_products(), key=lambda p: p.get("carbon_footprint_kg", 0), reverse=True)
    return {"greener_alternatives": [_offer(p) for p in items[:3]], "reason": "Ranked by carbon saved versus buying new."}


@real("/paas/basket/frequently-bought/read/v1")
def frequently_bought(tenant, params):
    others = [p for p in firestore_paas.list_products() if p["id"] != params.get("product_id")]
    return {"frequently_bought_together": [_offer(p) for p in others[:2]]}


@real("/paas/explain/decision/read/v1")
def explain_decision(tenant, params):
    return {"decision_id": params.get("decision_id"), "summary": "This price reflects condition grade A, local stock and a greener delivery option.",
            "factors": [{"factor": "Condition grade", "weight": "high", "detail": "Grade A, refurbished to as-new."},
                        {"factor": "Local stock", "weight": "medium", "detail": "In stock at a store near you."},
                        {"factor": "Carbon saved", "weight": "medium", "detail": "4.2 kg CO2e saved versus new."}]}


@real("/paas/pricing/personalized/offer/read/v1")
def personalized_offer(tenant, params):
    p = _product(params["product_id"])
    price = round(p["retail_price"] * 0.9, 2)
    return {"product_id": p["id"], "list_price": p["retail_price"], "your_price": price, "discount_pct": 10,
            "reason": "A returning-shopper offer from this seller.", "preview": True}


@real("/paas/return-risk/checkout/guidance/read/v1")
def return_risk(tenant, params):
    return {"product_id": params["product_id"], "return_risk": "low",
            "guidance": "This size runs true. Based on similar shoppers, a return is unlikely.", "preview": True}


@real("/paas/future-value/quote/read/v1")
def future_value_quote(tenant, params):
    p = _product(params["product_id"])
    years = int(params.get("years") or 2)
    value = round(p["retail_price"] * (0.6 ** years), 2)
    return {"product_id": p["id"], "years": years, "guaranteed_buy_back_usd": value,
            "quote_id": _oid("fv"), "preview": True}


def _env(product: Dict[str, Any]) -> Dict[str, Any]:
    # carbon_footprint_kg is the CO2e a shopper saves by buying this refurbished item instead of new,
    # so more saved means a better score (and the same ordering the "greener alternatives" list uses)
    saved = product.get("carbon_footprint_kg", 0)
    score = min(99, 55 + int(saved * 10))
    return {"environmental_score": score, "carbon_saved_kg": saved,
            "recyclable_pct": 86, "grade": "A" if score >= 90 else "B" if score >= 70 else "C"}


@real("/paas/environment/score/read/v1")
def env_score(tenant, params):
    p = _product(params["product_id"])
    return {"product_id": p["id"], **_env(p)}


@real("/paas/environment/offer-score/read/v1")
def env_offer_score(tenant, params):
    return {"offer_id": params["offer_id"], "carbon_footprint_kg": 3.1, "environmental_score": 84, "grade": "A"}


@real("/paas/environment/recycling-factor/read/v1")
def env_recycling(tenant, params):
    p = _product(params["product_id"])
    return {"product_id": p["id"], "recyclable_pct": 86, "notes": "Aluminium casing and battery are recoverable at certified recyclers."}


@real("/paas/parts/listing/read/v1")
def parts_listing(tenant, params):
    return {"parts": [{"part_id": "b27a6a6a-bb8e-5600-9d6c-995906c2ce47", "name": "Replacement battery module", "price": 24.0, "condition": "new"},
                      {"part_id": "f26963ab-cfad-5b33-bc4e-8dce5e5ed8bc", "name": "Eco strap (recycled)", "price": 12.5, "condition": "new"}]}


@real("/paas/feedback/review/read/v1")
def read_reviews(tenant, params):
    pid = params["product_id"]
    seeded = [{"review_id": "e3883a66-7abe-52e0-a562-1ec822b28198", "product_id": pid, "rating": 5, "comment": "Great as refurbished, saved money and carbon.", "by": "A shopper", "at": "2026-09-01"}]
    mine = [r for r in _state(tenant)["reviews"] if r["product_id"] == pid]
    return {"product_id": pid, "reviews": mine + seeded, "average_rating": 4.8}


@real("/paas/feedback/review/submit/v1")
def submit_review(tenant, params):
    review = {"review_id": _oid("rev"), "product_id": params["product_id"], "rating": int(params["rating"]),
              "comment": params.get("comment", ""), "by": _who(), "at": _now()}
    _state(tenant)["reviews"].insert(0, review)
    return {"status": "submitted", "review": review}


# ---------- PaaS: cart, wishlist, orders, reservations ----------
@real("/paas/order/cart/add/v1")
def cart_add(tenant, params):
    st = _state(tenant)
    p = _product(params["product_id"])
    qty = int(params["quantity"])
    line = next((l for l in st["cart"] if l["product_id"] == p["id"]), None)
    if line:
        line["quantity"] += qty
    else:
        st["cart"].append({"product_id": p["id"], "name": p["name"], "price": p["retail_price"], "quantity": qty})
    return {"status": "added", "cart": _cart_view(st)}


@real("/paas/order/cart/remove/v1")
def cart_remove(tenant, params):
    st = _state(tenant)
    st["cart"] = [l for l in st["cart"] if l["product_id"] != params["product_id"]]
    return {"status": "removed", "cart": _cart_view(st)}


def _cart_view(st) -> Dict[str, Any]:
    lines = st["cart"]
    total = round(sum(l["price"] * l["quantity"] for l in lines), 2)
    return {"lines": lines, "item_count": sum(l["quantity"] for l in lines), "total_usd": total}


@real("/paas/order/cart/read/v1")
def cart_read(tenant, params):
    return {"cart": _cart_view(_state(tenant))}


@real("/paas/order/checkout/place/v1")
def checkout(tenant, params):
    st = _state(tenant)
    if not st["cart"]:
        raise ValueError("Your cart is empty.")
    cart = _cart_view(st)
    order = {"order_id": _oid("ord"), "lines": list(st["cart"]), "total_usd": cart["total_usd"],
             "status": "placed", "payment_method": params.get("payment_method", "card"),
             "address": params.get("address"), "placed_at": _now(), "seller": tenant["name"]}
    st["orders"].insert(0, order)
    st["cart"] = []
    st["green_credits"] += int(cart["total_usd"] // 10)
    return {"status": "placed", "order": order, "green_credits": st["green_credits"]}


@real("/paas/order/read/customer/v1")
def read_orders(tenant, params):
    return {"orders": _state(tenant)["orders"]}


@real("/paas/order/cancel/customer/v1")
def cancel_order(tenant, params):
    st = _state(tenant)
    order = next((o for o in st["orders"] if o["order_id"] == params["order_id"]), None)
    if order is None:
        raise LookupError(f"No order {params['order_id']}")
    order["status"] = "cancelled"
    order["cancel_reason"] = params.get("reason")
    return {"status": "cancelled", "order": order}


@real("/paas/payment/invoice/read/v1")
def read_invoice(tenant, params):
    st = _state(tenant)
    order = next((o for o in st["orders"] if o["order_id"] == params["order_id"]), None)
    if order is None:
        raise LookupError(f"No order {params['order_id']}")
    return {"invoice": {"invoice_id": seed_id("invoice:" + order["order_id"]), "order_id": order["order_id"],
                        "total_usd": order["total_usd"], "status": "paid", "seller": tenant["name"], "issued_at": order["placed_at"]}}


@real("/paas/payment/gateway/process/v1")
def process_payment(tenant, params):
    return {"preview": True, "status": "succeeded", "payment_id": _oid("pay"), "amount": params.get("amount"),
            "currency": params.get("currency", "USD"), "gateway": f"{tenant['name']}'s payment provider",
            "message": "Payment processed through the seller's own gateway (preview)."}


@real("/paas/promotion/coupon/apply/v1")
def apply_coupon(tenant, params):
    return {"preview": True, "status": "applied", "code": params["code"], "discount_pct": 10,
            "message": "Coupon applied at checkout (preview)."}


@real("/paas/wishlist/item/add/v1")
def wishlist_add(tenant, params):
    st = _state(tenant)
    p = _product(params["product_id"])
    if not any(w["product_id"] == p["id"] for w in st["wishlist"]):
        st["wishlist"].insert(0, {"product_id": p["id"], "name": p["name"], "price": p["retail_price"]})
    return {"status": "added", "wishlist": st["wishlist"]}


@real("/paas/wishlist/item/remove/v1")
def wishlist_remove(tenant, params):
    st = _state(tenant)
    st["wishlist"] = [w for w in st["wishlist"] if w["product_id"] != params["product_id"]]
    return {"status": "removed", "wishlist": st["wishlist"]}


@real("/paas/wishlist/read/v1")
def wishlist_read(tenant, params):
    return {"wishlist": _state(tenant)["wishlist"]}


@real("/paas/green-credits/balance/read/v1")
def credits_balance(tenant, params):
    return {"balance": _state(tenant)["green_credits"], "value_usd": round(_state(tenant)["green_credits"] * 0.1, 2)}


@real("/paas/green-credits/redeem/v1")
def credits_redeem(tenant, params):
    st = _state(tenant)
    want = int(params["credits"])
    if want > st["green_credits"]:
        raise ValueError(f"You have {st['green_credits']} credits, cannot redeem {want}.")
    st["green_credits"] -= want
    return {"status": "redeemed", "redeemed": want, "balance": st["green_credits"], "value_usd": round(want * 0.1, 2)}


@real("/paas/reserve/item/create/v1")
def reserve_create(tenant, params):
    st = _state(tenant)
    p = _product(params["product_id"])
    res = {"reservation_id": _oid("res"), "product_id": p["id"], "name": p["name"], "store_id": params["store_id"],
           "pickup_by": params.get("pickup_by"), "status": "reserved", "at": _now()}
    st["reservations"].insert(0, res)
    return {"status": "reserved", "reservation": res}


@real("/paas/reserve/item/read/v1")
def reserve_read(tenant, params):
    return {"reservations": _state(tenant)["reservations"]}


@real("/paas/reserve/item/cancel/v1")
def reserve_cancel(tenant, params):
    st = _state(tenant)
    res = next((r for r in st["reservations"] if r["reservation_id"] == params["reservation_id"]), None)
    if res is None:
        raise LookupError(f"No reservation {params['reservation_id']}")
    res["status"] = "cancelled"
    return {"status": "cancelled", "reservation": res}


# ---------- PaaS: bidding ----------
def _new_bid(tenant, params, mode):
    p = _product(params["product_id"])
    offer = float(params["offer_price"])
    counter = round(max(offer, p["current_bidding_floor"] * 1.05), 2)
    bid = {"bid_id": _oid("bid"), "mode": mode, "product_id": p["id"], "name": p["name"], "offer_price": offer,
           "seller_counter": counter, "status": "open", "rounds": [{"by": _who(), "price": offer, "at": _now()},
                                                                    {"by": "seller", "price": counter, "at": _now()}], "at": _now()}
    _state(tenant)["bids"].insert(0, bid)
    return bid


@real("/paas/bid/ai/start/v1")
def bid_ai_start(tenant, params):
    bid = _new_bid(tenant, params, "ai")
    bid["bot_message"] = f"I can offer this at ${bid['seller_counter']}. Shall I try for less?"
    return {"status": "open", "bid": bid}


@real("/paas/bid/human/start/v1")
def bid_human_start(tenant, params):
    return {"status": "open", "bid": _new_bid(tenant, params, "human")}


def _bid(tenant, bid_id):
    bid = next((b for b in _state(tenant)["bids"] if b["bid_id"] == bid_id), None)
    if bid is None:
        raise LookupError(f"No bid {bid_id}")
    return bid


@real("/paas/bid/ai/customer-reply/v1")
def bid_ai_reply(tenant, params):
    bid = _bid(tenant, params["bid_id"])
    if bid["status"] != "open":
        raise ValueError(f"This bid is already {bid['status']}.")
    floor = _product(bid["product_id"])["current_bidding_floor"]
    action = params["action"]
    if action == "accept":
        bid["status"] = "accepted"
        bid["agreed_price"] = bid["seller_counter"]
    elif action == "decline":
        bid["status"] = "declined"
    else:
        price = float(params.get("price") or bid["offer_price"])
        bid["rounds"].append({"by": _who(), "price": price, "at": _now()})
        if price >= floor:
            # an offer at or above the seller's floor is accepted at the shopper's price
            bid["status"] = "accepted"
            bid["agreed_price"] = price
            bid["bot_message"] = f"Deal. ${price} it is."
        else:
            # the seller moves towards the shopper but never below its floor
            bid["seller_counter"] = round(max(floor, (price + bid["seller_counter"]) / 2), 2)
            bid["rounds"].append({"by": "seller", "price": bid["seller_counter"], "at": _now()})
            bid["bot_message"] = f"I can do ${bid['seller_counter']}." if bid["seller_counter"] > floor else f"${bid['seller_counter']} is my best price."
    return {"status": bid["status"], "bid": bid}


@real("/paas/bid/human/counter/customer/v1")
def bid_human_counter(tenant, params):
    bid = _bid(tenant, params["bid_id"])
    bid["rounds"].append({"by": _who(), "price": float(params["price"]), "at": _now()})
    return {"status": "countered", "bid": bid}


@real("/paas/bid/multi-seller/rank/read/v1")
def bid_rank(tenant, params):
    return {"request_id": params["request_id"], "offers": [
        {"seller": "GreenCycle", "price": 182.0, "delivery_days": 2, "condition": "refurbished", "reliability": 4.9, "rank": 1},
        {"seller": "EcoResale", "price": 179.0, "delivery_days": 5, "condition": "used", "reliability": 4.4, "rank": 2},
        {"seller": "ReNew Store", "price": 188.0, "delivery_days": 1, "condition": "refurbished", "reliability": 4.7, "rank": 3}]}


# ---------- PaaS / TaaS / SaaS: AI assistants ----------
def _assistant(topic):
    def handler(tenant, params):
        if "audio" in params:
            return {"preview": True, "transcript": "(voice input)", **vertex_ai.chat("Voice request", {"topic": topic})}
        return {"preview": True, **vertex_ai.chat(params.get("message", ""), {"topic": topic})}
    return handler


for _p in ("/paas/assistant/chat/text-to-text/v1", "/paas/assistant/chat/text-to-speech/v1",
           "/paas/assistant/voice/speech-to-text/v1", "/paas/assistant/voice/speech-to-speech/v1"):
    REAL[_p] = _assistant("shopping")
for _p in ("/taas/assistant/delivery/text-to-text/v1", "/taas/assistant/delivery/text-to-speech/v1",
           "/taas/assistant/delivery/speech-to-text/v1", "/taas/assistant/delivery/speech-to-speech/v1"):
    REAL[_p] = _assistant("delivery")
for _p in ("/saas/assistant/support/text-to-text/v1", "/saas/assistant/support/text-to-speech/v1",
           "/saas/assistant/support/speech-to-text/v1", "/saas/assistant/support/speech-to-speech/v1"):
    REAL[_p] = _assistant("support")
REAL["/paas/bid/ai/counter-offer/voice/v1"] = _assistant("bidding")


# ---------- TaaS: delivery, tracking, carbon ----------
_DELIVERY_OPTIONS = [
    {"option_id": "7db030e6-8d34-5f95-8a47-a0150cdc4412", "name": "Eco (electric van)", "days": 3, "price_usd": 0.0, "carbon_kg": 0.4, "environmental_score": 95},
    {"option_id": "3135db76-de09-567d-a064-a5a722aa5433", "name": "Standard", "days": 2, "price_usd": 2.5, "carbon_kg": 1.2, "environmental_score": 70},
    {"option_id": "819bca21-db42-56c0-843e-466f4bd10966", "name": "Express", "days": 1, "price_usd": 6.0, "carbon_kg": 2.8, "environmental_score": 45},
]


@real("/taas/delivery/option/list/v1")
def delivery_options(tenant, params):
    return {"destination_postcode": params.get("destination_postcode"), "options": _DELIVERY_OPTIONS}


@real("/taas/tracking/read/v1")
def track(tenant, params):
    return {"order_id": params["order_id"], "status": "in_transit", "carrier": "EcoExpress",
            "eta": "Tomorrow, 14:00-18:00", "events": [
                {"at": "2026-10-12 09:10", "event": "Picked up"},
                {"at": "2026-10-12 18:40", "event": "At Pune hub"},
                {"at": "2026-10-13 07:05", "event": "Out for delivery"}]}


@real("/taas/carbon/footprint/delivery/read/v1")
def carbon_delivery(tenant, params):
    return {"order_id": params["order_id"], "carbon_kg": 0.4, "method": "distance-based", "note": "Delivered by electric van."}


@real("/taas/carbon/footprint/offer/read/v1")
def carbon_offer(tenant, params):
    return {"offer_id": params["offer_id"], "carbon_kg": 1.2, "environmental_score": 70}


@real("/taas/environment/transport-score/read/v1")
def transport_score(tenant, params):
    scores = {"electric": 95, "van": 70, "air": 30}
    mode = str(params["transport_mode"]).lower()
    return {"transport_mode": params["transport_mode"], "environmental_score": scores.get(mode, 60)}


# ---------- SaaS: tickets, returns, repairs, trade-in, grading ----------
def _new_ticket(tenant, params, kind):
    st = _state(tenant)
    ticket = {"ticket_id": _oid("tkt"), "type": kind, "subject": params.get("subject") or f"{kind.title()} request",
              "status": "open", "order_id": params.get("order_id"), "product_id": params.get("product_id"),
              "messages": [{"by": _who(), "message": params.get("message") or params.get("description") or params.get("reason") or params.get("issue") or "", "at": _now()}],
              "at": _now(), "consumer": tenant["name"]}
    st["tickets"].insert(0, ticket)
    return ticket


@real("/saas/ticket/create/query/v1")
def ticket_query(tenant, params):
    return {"status": "open", "ticket": _new_ticket(tenant, params, "query")}


@real("/saas/ticket/create/return/v1")
def ticket_return(tenant, params):
    return {"status": "open", "ticket": _new_ticket(tenant, params, "return")}


@real("/saas/ticket/create/repair/v1")
def ticket_repair(tenant, params):
    return {"status": "open", "ticket": _new_ticket(tenant, params, "repair")}


@real("/saas/ticket/create/trade-in/v1")
def ticket_tradein(tenant, params):
    return {"status": "open", "ticket": _new_ticket(tenant, params, "trade-in")}


@real("/saas/ticket/read/customer/v1")
def read_tickets(tenant, params):
    return {"tickets": _state(tenant)["tickets"]}


def _find_ticket(tenant, ticket_id):
    ticket = next((t for t in _state(tenant)["tickets"] if t["ticket_id"] == ticket_id), None)
    if ticket is None:
        raise LookupError(f"No ticket {ticket_id}")
    return ticket


@real("/saas/ticket/reply/customer/v1")
def reply_ticket(tenant, params):
    ticket = _find_ticket(tenant, params["ticket_id"])
    ticket["messages"].append({"by": _who(), "message": params["message"], "at": _now()})
    return {"status": "replied", "ticket": ticket}


@real("/saas/ticket/status/read/v1")
def ticket_status(tenant, params):
    ticket = _find_ticket(tenant, params["ticket_id"])
    return {"ticket_id": ticket["ticket_id"], "status": ticket["status"], "type": ticket["type"], "messages": ticket["messages"]}


@real("/saas/return/request/create/v1")
def return_request(tenant, params):
    return {"status": "open", "return": _new_ticket(tenant, {**params, "subject": "Guided return"}, "return"),
            "steps": ["Pack the item", "Print the label", "Drop off or request pickup"]}


@real("/saas/repair/request/create/v1")
def repair_request(tenant, params):
    return {"status": "open", "repair": _new_ticket(tenant, {**params, "subject": "Repair request"}, "repair")}


@real("/saas/recycling/request/create/v1")
def recycling_request(tenant, params):
    return {"status": "open", "recycling": _new_ticket(tenant, {**params, "subject": "Recycling request"}, "recycling")}


@real("/saas/grading/photo/submit/v1")
def grading_submit(tenant, params):
    upload = cloud_storage.create_upload_url(params.get("return_id", "item"), "image/jpeg")
    return {"preview": True, "status": "submitted", "upload": upload, "return_id": params.get("return_id"),
            "message": "Photos submitted. A grade and value will be ready before you ship."}


@real("/saas/grading/result/read/v1")
def grading_result(tenant, params):
    return {"return_id": params.get("return_id"), "grade": "B", "estimated_value_usd": 96.0,
            "route": "refurbish", "reason": "Light wear on the casing; fully working.", "preview": True}


@real("/saas/trade-in/request/create/v1")
def tradein_request(tenant, params):
    return {"status": "open", "trade_in": _new_ticket(tenant, {**params, "subject": "Trade-in request"}, "trade-in")}


@real("/saas/trade-in/valuation/read/v1")
def tradein_valuation(tenant, params):
    return {"trade_in_id": params.get("trade_in_id"), "estimated_value_usd": 108.0,
            "valuation_id": _oid("val"), "reason": "AI estimate from condition and current demand.", "preview": True}


@real("/saas/trade-in/offer/accept/v1")
def tradein_accept(tenant, params):
    st = _state(tenant)
    st["green_credits"] += 50
    return {"status": "accepted", "trade_in_id": params.get("trade_in_id"), "credited_usd": 108.0,
            "green_credits": st["green_credits"]}


@real("/saas/recommendation/reuse/read/v1")
def reuse_advice(tenant, params):
    return {"item_id": params.get("item_id"), "advice": "This item is a strong resale candidate; refurbish and relist.",
            "route": "reuse", "preview": True}


@real("/saas/recommendation/recycle/read/v1")
def recycle_advice(tenant, params):
    return {"item_id": params.get("item_id"), "advice": "Beyond economic repair; send to a certified recycler to recover 86% of materials.",
            "route": "recycle", "preview": True}


@real("/saas/explain/decision/read/v1")
def saas_explain(tenant, params):
    return {"decision_id": params.get("decision_id"), "summary": "Graded B and routed to refurbishment.",
            "factors": [{"factor": "Condition", "detail": "Light cosmetic wear, fully working."},
                        {"factor": "Demand", "detail": "High resale demand for this model."}]}


@real("/saas/scorecard/customer/read/v1")
def scorecard(tenant, params):
    st = _state(tenant)
    return {"value_recovered_usd": 216.0 + len(st["orders"]) * 10, "waste_diverted_kg": 7.4,
            "carbon_saved_kg": 12.6, "green_credits": st["green_credits"], "orders": len(st["orders"])}


@real("/saas/dropoff/status/read/v1")
def dropoff_status(tenant, params):
    return {"dropoff_id": params.get("dropoff_id"), "status": "in_transit",
            "events": [{"at": _now(), "event": "Received at store"}], "preview": True}


# ---- Registration: give every Customer-actor endpoint a handler (real, else a stand-in) ----
def register_customer_handlers(handlers: Dict[str, Callable]) -> int:
    from cloud_sql.services.maas.endpoints import endpoint_registry
    added = 0
    for e in endpoint_registry.list_endpoints():
        if e["actor"] != "Customer" or e["path"] in handlers:
            continue
        handlers[e["path"]] = REAL.get(e["path"]) or _standin(e)
        added += 1
    return added
