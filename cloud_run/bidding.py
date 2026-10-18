"""
Cloud Run - multi-seller bidding.
A shopper opens a room for a product with a maximum budget. The demo sellers (made-up businesses) that carry that kind of item
each make an offer, the offers are ranked on price, seller rating, delivery time and how much new manufacture the choice avoids,
and the best fit inside the budget wins and is awarded the room straight away (the award is the System's step, which a shopper cannot call). Offers are worked out from the product's own price, so the same product and budget
always give the same room; nothing here calls an outside service.

The sellers stand in for real seller accounts. When those exist, make_offers is the only function that changes: it would collect
the offers the sellers submitted instead of working them out.
"""

import hashlib
from typing import Any, Dict, List, Optional

# discount: how far below the list price the seller starts; delivery_days: its usual time to the shopper
DEMO_SELLERS: List[Dict[str, Any]] = [
    {"seller_id": "demo-citymart", "name": "CityMart Retail", "type": "Retailer", "rating": 4.5, "discount": 0.12, "delivery_days": 2, "conditions": ["new", "refurbished"]},
    {"seller_id": "demo-greenloop", "name": "GreenLoop Refurbishers", "type": "Refurbisher", "rating": 4.7, "discount": 0.30, "delivery_days": 4, "conditions": ["refurbished"]},
    {"seller_id": "demo-recommerce", "name": "ReCommerce Outlet", "type": "Outlet", "rating": 4.1, "discount": 0.24, "delivery_days": 3, "conditions": ["refurbished", "used"]},
    {"seller_id": "demo-secondspin", "name": "Second Spin Traders", "type": "Retailer", "rating": 3.6, "discount": 0.36, "delivery_days": 6, "conditions": ["used", "refurbished"]},
]

CONDITIONS = ("new", "refurbished", "used")

def product_condition(product: Dict[str, Any]) -> str:
    text = str(product.get("condition", "")).lower()
    for name in ("refurb", "used", "new"):
        if name in text:
            return {"refurb": "refurbished"}.get(name, name)
    return "refurbished"

def _jitter(seller_id: str, product_id: str) -> float:
    """A small, steady difference between sellers (-3% to +3%) so offers are not all the same shape."""
    digest = int(hashlib.sha1(f"{seller_id}:{product_id}".encode()).hexdigest()[:6], 16)
    return ((digest % 7) - 3) / 100

def eligible_sellers(product: Dict[str, Any], condition: Optional[str] = None, min_rating: float = 0.0) -> List[Dict[str, Any]]:
    wanted = condition or None
    return [s for s in DEMO_SELLERS if s["rating"] >= min_rating and (wanted is None or wanted in s["conditions"])]

def make_offers(product: Dict[str, Any], condition: Optional[str] = None, min_rating: float = 0.0) -> List[Dict[str, Any]]:
    list_price = float(product["retail_price"])
    floor = float(product.get("current_bidding_floor") or list_price * 0.5)
    own = product_condition(product)
    offers = []
    for seller in eligible_sellers(product, condition, min_rating):
        price = list_price * (1 - seller["discount"] + _jitter(seller["seller_id"], product["id"]))
        price = round(max(price, floor * 0.85), 2)
        offered = condition or (own if own in seller["conditions"] else seller["conditions"][0])
        offers.append({"seller_id": seller["seller_id"], "seller_name": seller["name"], "seller_type": seller["type"], "seller_rating": seller["rating"],
                       "offer_price": price, "condition": offered, "delivery_days": seller["delivery_days"]})
    return offers

def _score(offer: Dict[str, Any], budget: float) -> float:
    """Higher is better: cheaper, better rated, faster, and reused instead of new."""
    reuse = {"new": 0.0, "refurbished": 6.0, "used": 8.0}[offer["condition"]]
    return round(60 - 50 * (offer["offer_price"] / budget) + 4 * offer["seller_rating"] - 1.5 * offer["delivery_days"] + reuse, 2)

def rank(offers: List[Dict[str, Any]], budget: float) -> List[Dict[str, Any]]:
    """Every offer with its score and whether it is inside the budget, best first. Offers over the budget never win."""
    scored = [{**o, "within_budget": o["offer_price"] <= budget, "score": _score(o, budget)} for o in offers]
    scored.sort(key=lambda o: (not o["within_budget"], -o["score"]))
    return [{**o, "rank": i + 1} for i, o in enumerate(scored)]

def winner(ranked: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return ranked[0] if ranked and ranked[0]["within_budget"] else None

def build_room(room_id: str, product: Dict[str, Any], budget: float, quantity: int = 1, condition: Optional[str] = None,
               min_rating: float = 0.0, now: str = "") -> Dict[str, Any]:
    ranked = rank(make_offers(product, condition, min_rating), budget)
    best = winner(ranked)
    if best:
        note = f"{len(ranked)} sellers made offers. {best['seller_name']} is the best fit at ${best['offer_price']:.2f} and wins the room."
    elif ranked:
        note = f"{len(ranked)} sellers made offers, but none is within ${budget:.2f}. The lowest is ${min(o['offer_price'] for o in ranked):.2f}."
    else:
        note = "No seller carries this item in that condition."
    return {"room_id": room_id, "request_id": room_id, "product_id": product["id"], "product_name": product["name"], "customer_max_budget": budget,
            "quantity": quantity, "status": "AWARDED" if best else "NO_MATCH", "participating_sellers": len(ranked),
            "offers": ranked, "winning_best_fit": best, "carbon_saving_vs_new": None, "note": note, "opened_at": now}

def find_product(products: List[Dict[str, Any]], description: str) -> Optional[Dict[str, Any]]:
    """The product whose name, category and description share the most words with what the shopper asked for."""
    words = {w for w in "".join(c.lower() if c.isalnum() else " " for c in description).split() if len(w) > 2}
    best, best_hits = None, 0
    for p in products:
        if p.get("archived"):
            continue
        text = " ".join(str(p.get(k, "")) for k in ("name", "category", "description")).lower()
        hits = sum(1 for w in words if w in text)
        if hits > best_hits:
            best, best_hits = p, hits
    return best
