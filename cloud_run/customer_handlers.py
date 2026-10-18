"""
Cloud Run - Customer portal handlers
What a Customer (shopper) call does once it has passed the gate, by catalog path. A shopper has a separate account
with each consumer they shop with, so every shopper's data (profile, cart, wishlist, orders, tickets, reservations,
reviews, green credits) is kept in Firestore per (consumer, shopper). A shopper's order, ticket and return also become the
consumer's own records, so its staff see and work on them, and what staff do shows back to the shopper.

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
from cloud_run import assistant_facts, bid_flow, bidding, mapsupport, rules
from cloud_run.photos import decode_photo, take_turn
from firestore import store
from firestore.services.taas import firestore_taas

# ---- Per-shopper state, kept in Firestore per (consumer, shopper email) ----
_ids = itertools.count(1)



def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _who() -> str:
    """The shopper making this call (their email). The gate sets it for Customer-side endpoints."""
    email = ops.CUSTOMER.get() or ""
    return email.strip().lower()


def _state(tenant) -> Dict[str, Any]:
    email = _who()
    return store.kdoc("shoppers", email, lambda: {
        "profile": {"email": email, "account_type": "individual", "full_name": "", "phone": "",
                    "preferred_language": "en", "address": None, "verified": False,
                    "consumer": tenant["name"], "joined": _now()},
        "cart": [], "wishlist": [], "orders": [], "tickets": [], "reservations": [],
        "reviews": [], "green_credits": 0, "bids": [],
    }, tenant_id=tenant["tenant_id"])


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
        records = store.kdoc("shopper_records", f"{_who()}__{feature}", lambda: {"items": []}, tenant_id=tenant["tenant_id"])["items"]
        if is_read:
            items = [r for r in records
                     if all(str(r["params"].get(k)) == str(v) for k, v in params.items() if v not in (None, "") and k in r["params"])]
            return {"preview": True, "items": items,
                    "note": "Preview: shows what you recorded for this feature in this session. Real data arrives once the backend is connected."}
        record = {"id": _oid("pv"), "action": endpoint["sub_category"].replace("/", " "), "endpoint": endpoint["path"],
                  "params": params, "at": _now(), "by": _who(), "status": "recorded"}
        records.insert(0, record)
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
    rules.customer_language_ok(tenant["tenant_id"], params["language"])
    _state(tenant)["profile"]["preferred_language"] = params["language"]
    return {"status": "ok", "preferred_language": params["language"]}


@real("/maas/customer-account/data/export/v1")
def export_data(tenant, params):
    st = _state(tenant)
    return {"format": params.get("format", "json"), "generated_at": _now(), "data": st,
            "message": "Your data, ready to download."}


def _stores() -> List[Dict[str, Any]]:
    """The consumer's stores that are open to shoppers."""
    return [s for s in store.rows("stores", "store_id") if s.get("active", True)]


@real("/maas/location/store/list/v1")
def list_stores(tenant, params):
    return {"stores": _stores()}


@real("/maas/location/store/nearby/find/v1")
def nearby_store(tenant, params):
    stores = _stores()
    if not stores:
        return {"nearest": None, "stores": []}
    ranked = mapsupport.stores_by_distance(float(params["latitude"]), float(params["longitude"]), stores)
    return {"nearest": ranked[0] if ranked else None, "stores": ranked}


@real("/maas/assistant/account-help/ask/v1")
def account_help(tenant, params):
    context = {"topic": "account and login", "language": params.get("language") or "en", "facts": assistant_facts.build(tenant, "account and login")}
    return {**vertex_ai.chat(params["question"], context)}


# ---------- PaaS: catalog ----------
def _offer(product: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": product["id"], "name": product["name"], "sku": product.get("sku"), "category": product.get("category"),
            "price": product.get("retail_price"), "bidding_floor": product.get("current_bidding_floor"),
            "condition": product.get("condition"), "stock": product.get("stock"), "image_url": product.get("image_url"),
            "carbon_footprint_kg": product.get("carbon_footprint_kg")}


@real("/paas/catalog/product/view/v1")
def view_product(tenant, params):
    p = _product(params["product_id"])
    found = [r for r in store.rows("reviews", "review_id", newest_first=True) if r["product_id"] == p["id"]]
    return {"product": {**_offer(p), "rating": round(sum(r["rating"] for r in found) / len(found), 1) if found else None, "reviews": len(found),
                        "passport_id": passport_id(p["id"]), "seller": tenant["name"],
                        "translation": (p.get("translations") or {}).get(_state(tenant)["profile"].get("preferred_language"))}}


@real("/paas/catalog/search/text/v1")
def search_text(tenant, params):
    q = str(params["query"]).lower()
    hits = [_offer(p) for p in firestore_paas.list_products() if q in p["name"].lower() or q in p.get("category", "").lower()]
    return {"query": params["query"], "results": hits, "count": len(hits)}


@real("/paas/store-stock/read/v1")
def store_stock(tenant, params):
    p = _product(params["product_id"])
    held = p.get("stock_by_store") or {}
    return {"product_id": p["id"], "name": p["name"],
            "by_store": [{"store_id": s["store_id"], "store": s["name"], "in_stock": int(held.get(s["store_id"], 0))} for s in _stores()]}


@real("/paas/passport/read/v1")
def read_passport(tenant, params):
    pid = params.get("passport_id", "")
    found = next((x for x in store.rows("passports", "passport_id") if x["passport_id"] == pid), None)
    return {"passport": found or {"passport_id": pid, "origin": "", "owners": 0, "repairs": [], "grades": [],
                                  "carbon_saved_kg": 0, "recyclable_pct": 0}}


@real("/paas/passport/scan/v1")
def scan_passport(tenant, params):
    return read_passport(tenant, {"passport_id": params.get("qr_code", "")})


@real("/paas/recommendation/product/read/v1")
def recommend_products(tenant, params):
    st = _state(tenant)
    products = firestore_paas.list_products()
    by_id = {p["id"]: p for p in products}
    tid = tenant["tenant_id"]
    use = set(rules.personalization(tid)["enabled_signals"])  # the signals the consumer lets the recommendations learn from
    fresh = lambda stamp: rules.within_retention(tid, stamp)
    cart_ids, wish_ids = {l["product_id"] for l in st["cart"]}, {w["product_id"] for w in st["wishlist"]}
    order_ids = {l["product_id"] for o in st["orders"] for l in o["lines"]}
    bid_ids = {b["product_id"] for b in st["bids"]}
    seen = cart_ids | wish_ids | order_ids | bid_ids  # never offer what the shopper already has
    learned = ((cart_ids if "cart" in use else set()) | (wish_ids if "wishlist" in use else set())
               | ({l["product_id"] for o in st["orders"] if fresh(o.get("placed_at")) for l in o["lines"]} if "orders" in use else set())
               | ({b["product_id"] for b in st["bids"] if fresh(b.get("at"))} if "bids" in use else set()))
    if params.get("product_id"):
        seen.add(params["product_id"])
        learned.add(params["product_id"])
    liked = {by_id[i].get("category") for i in learned if i in by_id}
    # what the shopper has not met yet, in the categories they have shown interest in first, then the greenest
    pool = [p for p in products if p["id"] not in seen]
    pool.sort(key=lambda p: (p.get("category") not in liked, -p.get("carbon_footprint_kg", 0)))
    items = [_offer(p) for p in pool[: int(params.get("limit") or 3)]]
    reason = "Picked from what you have in your cart, wishlist, orders and bids." if learned else "Popular with shoppers, greenest first. It sharpens as you browse and buy."
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
    return {"decision_id": params.get("decision_id"), "summary": "", "factors": []}


@real("/paas/pricing/personalized/offer/read/v1")
def personalized_offer(tenant, params):
    p = _product(params["product_id"])
    today = datetime.date.today().isoformat()
    live = [o for o in _state(tenant).get("offers", []) if o.get("discount_pct") and (not o.get("expires") or str(o["expires"])[:10] >= today)]
    best = max(live, key=lambda o: o["discount_pct"], default=None)
    listed = float(p["retail_price"])
    if best is None:
        return {"product_id": p["id"], "list_price": listed, "your_price": listed, "discount_pct": 0, "reason": "No offer for you right now."}
    price = max(round(listed * (1 - best["discount_pct"] / 100), 2), float(p["current_bidding_floor"]))  # never below the seller's floor
    return {"product_id": p["id"], "list_price": listed, "your_price": price, "discount_pct": round((listed - price) / listed * 100, 1),
            "reason": f"{best['title']} (sent to your customer group).", "offer_id": best["offer_id"]}


@real("/paas/return-risk/checkout/guidance/read/v1")
def return_risk(tenant, params):
    return {"product_id": params["product_id"], "return_risk": None,
            "guidance": "", "preview": True}


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
            "recyclable_pct": 0, "grade": "A" if score >= 90 else "B" if score >= 70 else "C"}


@real("/paas/environment/score/read/v1")
def env_score(tenant, params):
    p = _product(params["product_id"])
    return {"product_id": p["id"], **_env(p)}


@real("/paas/environment/offer-score/read/v1")
def env_offer_score(tenant, params):
    return {"offer_id": params["offer_id"], "carbon_footprint_kg": None, "environmental_score": None, "grade": None}


@real("/paas/environment/recycling-factor/read/v1")
def env_recycling(tenant, params):
    p = _product(params["product_id"])
    return {"product_id": p["id"], "recyclable_pct": 0, "notes": ""}


@real("/paas/parts/listing/read/v1")
def parts_listing(tenant, params):
    return {"parts": store.rows("parts", "part_id")}


@real("/paas/feedback/review/read/v1")
def read_reviews(tenant, params):
    pid = params["product_id"]
    found = [r for r in store.rows("reviews", "review_id", newest_first=True) if r["product_id"] == pid]
    return {"product_id": pid, "reviews": found,
            "average_rating": round(sum(r["rating"] for r in found) / len(found), 1) if found else None}


@real("/paas/feedback/review/submit/v1")
def submit_review(tenant, params):
    review = {"review_id": _oid("rev"), "product_id": params["product_id"], "rating": int(params["rating"]),
              "comment": params.get("comment", ""), "by": _who(), "at": _now()}
    store.rows("reviews", "review_id", newest_first=True).insert(0, review)
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
    ops._orders().insert(0, {"order_id": order["order_id"], "customer": st["profile"].get("full_name") or _who(), "customer_email": _who(),
                              "items": ", ".join(f"{l['name']} x{l['quantity']}" for l in order["lines"]), "lines": list(order["lines"]), "total": order["total_usd"],
                              "status": "placed", "placed": _now()[:10]})
    st["cart"] = []
    st["green_credits"] += int(round(cart["total_usd"] * rules.green_rules(tenant["tenant_id"])["earn_per_unit"], 6))
    return {"status": "placed", "order": order, "green_credits": st["green_credits"]}


@real("/paas/order/read/customer/v1")
def read_orders(tenant, params):
    # what the consumer's staff have done to an order (paid, shipped, delivered) shows here
    staff = {o["order_id"]: o for o in ops._orders()}
    orders = _state(tenant)["orders"]
    return {"orders": [{**o, "status": staff[o["order_id"]]["status"]} if o["order_id"] in staff and o["status"] != "cancelled" else o for o in orders]}


@real("/paas/order/cancel/customer/v1")
def cancel_order(tenant, params):
    st = _state(tenant)
    order = next((o for o in st["orders"] if o["order_id"] == params["order_id"]), None)
    if order is None:
        raise LookupError(f"No order {params['order_id']}")
    staff = next((o for o in ops._orders() if o["order_id"] == order["order_id"]), None)
    if staff is not None:
        ops.update_order_status(order["order_id"], "cancelled")  # refused when the order has already shipped
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
    each = rules.green_rules(tenant["tenant_id"])["redeem_value"]
    return {"balance": _state(tenant)["green_credits"], "value_usd": round(_state(tenant)["green_credits"] * each, 2), "credit_value_usd": each}


@real("/paas/green-credits/redeem/v1")
def credits_redeem(tenant, params):
    st = _state(tenant)
    want = int(params["credits"])
    if want > st["green_credits"]:
        raise ValueError(f"You have {st['green_credits']} credits, cannot redeem {want}.")
    st["green_credits"] -= want
    return {"status": "redeemed", "redeemed": want, "balance": st["green_credits"], "value_usd": round(want * rules.green_rules(tenant["tenant_id"])["redeem_value"], 2)}


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
    rules.check_offer(tenant["tenant_id"], p, offer)
    counter = round(max(offer, rules.effective_floor(tenant["tenant_id"], p) * 1.05), 2)
    bid = {"bid_id": _oid("bid"), "mode": mode, "product_id": p["id"], "name": p["name"], "offer_price": offer,
           "seller_counter": counter, "status": "open", "rounds": [{"by": _who(), "price": offer, "at": _now()},
                                                                    {"by": "seller", "price": counter, "at": _now()}], "at": _now()}
    _state(tenant)["bids"].insert(0, bid)
    bid_flow.register(tenant, bid["bid_id"], _who())
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
    if rules.expired(tenant["tenant_id"], bid):
        raise ValueError("This bid's window has closed. Please start a new bid.")
    floor = rules.effective_floor(tenant["tenant_id"], _product(bid["product_id"]))
    action = params["action"]
    if action == "accept":
        bid_flow.hand_off(tenant, bid, bid["seller_counter"], "shopper")
    elif action == "decline":
        bid["status"] = "declined"
    else:
        price = float(params.get("price") or bid["offer_price"])
        bid["rounds"].append({"by": _who(), "price": price, "at": _now()})
        if price >= floor:
            # an offer at or above the seller's floor is accepted at the shopper's price
            bid_flow.hand_off(tenant, bid, price, "AI")
        elif sum(1 for r in bid["rounds"] if r["by"] == "seller") > rules.ai_limits(tenant["tenant_id"])["max_rounds"]:
            # the bot has used up the counters the seller allows it
            bid["status"] = "declined"
            bid["bot_message"] = f"I cannot go lower than ${bid['seller_counter']:.2f}. Thank you for bidding."
        else:
            # the seller moves towards the shopper but never below its floor
            bid["seller_counter"] = round(max(floor, (price + bid["seller_counter"]) / 2), 2)
            bid["rounds"].append({"by": "seller", "price": bid["seller_counter"], "at": _now()})
            bid["bot_message"] = f"I can do ${bid['seller_counter']}." if bid["seller_counter"] > floor else f"${bid['seller_counter']} is my best price."
    return {"status": bid["status"], "bid": bid}


@real("/paas/bid/human/counter/customer/v1")
def bid_human_counter(tenant, params):
    bid = _bid(tenant, params["bid_id"])
    if rules.expired(tenant["tenant_id"], bid):
        raise ValueError("This bid's window has closed. Please start a new bid.")
    bid["rounds"].append({"by": _who(), "price": float(params["price"]), "at": _now()})
    return {"status": "countered", "bid": bid}


def open_room(tenant, product, max_budget, quantity=1, condition=None):
    """Opens a multi-seller room for the signed-in shopper: the demo sellers make their offers and the best fit inside the budget wins."""
    if max_budget <= 0:
        raise ValueError("Enter a budget above zero.")
    if condition and condition not in bidding.CONDITIONS:
        raise ValueError("Condition must be new, refurbished or used.")
    wanted = rules.eligibility(tenant["tenant_id"])
    if int(product.get("stock") or 0) < max(wanted["min_stock"], int(quantity or 1)):
        raise ValueError("No seller has enough of this item in stock for the room.")
    room = bidding.build_room(new_id(), product, round(float(max_budget), 2), int(quantity or 1), condition, min_rating=wanted["min_rating"], now=_now())
    rooms = _state(tenant).setdefault("bid_rooms", [])
    rooms.insert(0, room)
    del rooms[20:]  # a shopper keeps their latest rooms
    return room


def _room(tenant, request_id):
    room = next((r for r in _state(tenant).get("bid_rooms", []) if r["request_id"] == request_id), None)
    if room is None:
        raise LookupError(f"No bidding room {request_id}")
    return room


@real("/paas/bid/multi-seller/open/v1")
def bid_open(tenant, params):
    product = bidding.find_product(firestore_paas.list_products(), params["description"])
    if product is None:
        raise ValueError("No product matches that description. Name the item, for example 'refurbished smartphone'.")
    budget = params.get("max_price") or product["retail_price"]
    return open_room(tenant, product, budget, params.get("quantity") or 1, params.get("condition"))


@real("/paas/bid/multi-seller/rank/read/v1")
def bid_rank(tenant, params):
    room = _room(tenant, params["request_id"])
    return {"request_id": room["request_id"], "status": room["status"], "offers": room["offers"], "winning_best_fit": room["winning_best_fit"], "note": room["note"]}


# ---------- PaaS / TaaS / SaaS: AI assistants ----------
def _assistant(topic):
    def handler(tenant, params):
        context = {"topic": topic, "language": params.get("language") or "en", "facts": assistant_facts.build(tenant, topic)}
        if "audio" in params:
            return {"preview": True, "transcript": "(voice input)", **vertex_ai.chat("Voice request", context)}
        return {**vertex_ai.chat(params.get("message", ""), context)}
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
def _delivery_options() -> List[Dict[str, Any]]:
    return store.kdoc("config", "delivery_options", lambda: {"options": []})["options"]


def _shipment_for(order_id: str):
    return next((s for s in firestore_taas.list_shipments() if s.get("order_id") == order_id), None)


@real("/taas/delivery/option/list/v1")
def delivery_options(tenant, params):
    return {"destination_postcode": params.get("destination_postcode"), "options": _delivery_options()}


@real("/taas/tracking/read/v1")
def track(tenant, params):
    s = _shipment_for(params["order_id"])
    if s is None:
        return {"order_id": params["order_id"], "status": "not_shipped", "carrier": "", "eta": "", "events": []}
    return {"order_id": params["order_id"], "status": s["status"], "carrier": s.get("carrier", ""), "eta": s.get("eta", ""), "events": s.get("events", [])}


@real("/taas/carbon/footprint/delivery/read/v1")
def carbon_delivery(tenant, params):
    s = _shipment_for(params["order_id"])
    if s is None:
        return {"order_id": params["order_id"], "carbon_kg": None, "method": "", "note": "This order has not shipped yet."}
    return {"order_id": params["order_id"], "carbon_kg": s.get("co2_kg"), "method": s.get("mode", ""), "note": s.get("carbon_note", "")}


@real("/taas/carbon/footprint/offer/read/v1")
def carbon_offer(tenant, params):
    return {"offer_id": params["offer_id"], "carbon_kg": None, "environmental_score": None}


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
    text = ticket["messages"][0]["message"]
    ops._tickets().insert(0, {"ticket_id": ticket["ticket_id"], "customer": st["profile"].get("full_name") or _who(), "customer_email": _who(),
                               "subject": ticket["subject"], "type": kind, "status": "open",
                               "messages": [{"from": "Customer", "text": text}] if text else []})
    if kind == "return":
        order = next((o for o in st["orders"] if o["order_id"] == params.get("order_id")), None)
        ops._returns().insert(0, {"return_id": ticket["ticket_id"], "order_id": params.get("order_id"), "customer": st["profile"].get("full_name") or _who(),
                                   "item": ", ".join(l["name"] for l in order["lines"]) if order else "", "reason": text,
                                   "amount": order["total_usd"] if order else 0, "status": "requested"})
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
    return {"tickets": [_ticket_view(t) for t in _state(tenant)["tickets"]]}


def _ticket_view(ticket):
    """The shopper's ticket, with the status and the conversation the consumer's staff have added."""
    staff = next((t for t in ops._tickets() if t["ticket_id"] == ticket["ticket_id"]), None)
    if staff is None:
        return ticket
    thread = [{"by": m.get("author") or ("You" if m["from"] == "Customer" else "Support"), "message": m["text"], "at": m.get("at", ""), "from": m["from"]}
              for m in staff["messages"]]
    return {**ticket, "status": staff["status"], "messages": thread or ticket["messages"]}


def _find_ticket(tenant, ticket_id):
    ticket = next((t for t in _state(tenant)["tickets"] if t["ticket_id"] == ticket_id), None)
    if ticket is None:
        raise LookupError(f"No ticket {ticket_id}")
    return ticket


@real("/saas/ticket/reply/customer/v1")
def reply_ticket(tenant, params):
    ticket = _find_ticket(tenant, params["ticket_id"])
    ticket["messages"].append({"by": _who(), "message": params["message"], "at": _now()})
    staff = next((t for t in ops._tickets() if t["ticket_id"] == ticket["ticket_id"]), None)
    if staff is not None:
        staff["messages"].append({"from": "Customer", "text": params["message"], "at": _now()})
        if staff["status"] in ("resolved", "closed"):
            staff["status"] = "open"  # a reply reopens it
    return {"status": "replied", "ticket": _ticket_view(ticket)}


@real("/saas/ticket/status/read/v1")
def ticket_status(tenant, params):
    ticket = _find_ticket(tenant, params["ticket_id"])
    view = _ticket_view(ticket)
    return {"ticket_id": view["ticket_id"], "status": view["status"], "type": view["type"], "messages": view["messages"]}


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
    """Grades the first photo with Gemini and keeps the result for this return, so the shopper sees it before shipping."""
    return_id = params.get("return_id")
    photos = params.get("photos") or []
    if isinstance(photos, str):
        photos = [photos]
    if not photos:
        raise ValueError("Add a photo of the item.")
    image, mime = decode_photo(photos[0])
    take_turn(_who())
    result = vertex_ai.grade_return_photo(return_id, image, mime)
    st = _state(tenant)
    st.setdefault("gradings", {})[str(return_id)] = {"grade": result["ai_evaluated_grade"], "recovery_percentage": result["predicted_recovery_percentage"],
                                                     "route": result["recommended_channel"], "defects": result["defects"],
                                                     "reason": result["reasoning"], "graded_at": _now()}
    return {"status": "graded" if result["ai_evaluated_grade"] else "not_graded", "return_id": return_id, **st["gradings"][str(return_id)],
            "message": "Graded from your photo. The value shown is an estimate until the item is inspected."}


@real("/saas/grading/result/read/v1")
def grading_result(tenant, params):
    found = _state(tenant).get("gradings", {}).get(str(params.get("return_id")))
    if not found:
        return {"return_id": params.get("return_id"), "grade": None, "reason": "No photo has been graded for this return yet. Submit a photo first."}
    return {"return_id": params.get("return_id"), **found}


@real("/saas/trade-in/request/create/v1")
def tradein_request(tenant, params):
    return {"status": "open", "trade_in": _new_ticket(tenant, {**params, "subject": "Trade-in request"}, "trade-in")}


@real("/saas/trade-in/valuation/read/v1")
def tradein_valuation(tenant, params):
    return {"trade_in_id": params.get("trade_in_id"), "estimated_value_usd": 0,
            "valuation_id": _oid("val"), "reason": "", "preview": True}


@real("/saas/trade-in/offer/accept/v1")
def tradein_accept(tenant, params):
    st = _state(tenant)
    return {"status": "accepted", "trade_in_id": params.get("trade_in_id"), "credited_usd": 0,
            "green_credits": st["green_credits"]}


@real("/saas/recommendation/reuse/read/v1")
def reuse_advice(tenant, params):
    return {"item_id": params.get("item_id"), "advice": "",
            "route": "", "preview": True}


@real("/saas/recommendation/recycle/read/v1")
def recycle_advice(tenant, params):
    return {"item_id": params.get("item_id"), "advice": "",
            "route": "", "preview": True}


@real("/saas/explain/decision/read/v1")
def saas_explain(tenant, params):
    return {"decision_id": params.get("decision_id"), "summary": "", "factors": []}


@real("/saas/scorecard/customer/read/v1")
def scorecard(tenant, params):
    st = _state(tenant)
    return {"value_recovered_usd": 0, "waste_diverted_kg": 0,
            "carbon_saved_kg": 0, "green_credits": st["green_credits"], "orders": len(st["orders"])}


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
