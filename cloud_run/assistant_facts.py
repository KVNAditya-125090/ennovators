"""
Cloud Run - what the assistants may say.
A short list of facts about one consumer's shop, built from its own records for each question, so an assistant answers from
the real catalog, delivery options and policies and never from memory. Kept small on purpose (it is sent with every question).
"""

from typing import Any, Dict, List

from firestore import store
from firestore.services.paas import firestore_paas
from firestore.users.consumer import operations as ops

def _products() -> List[str]:
    return [f"- {p['name']}: ${p['retail_price']:.2f}, {p.get('condition', '')}, {p.get('stock', 0)} in stock, carbon saved {p.get('carbon_footprint_kg', 0)} kg"
            for p in firestore_paas.list_products() if not p.get("archived")][:20]

def _delivery() -> List[str]:
    options = store.kdoc("config", "delivery_options", lambda: {"options": []})["options"]
    rules = ops.delivery_rules()
    lines = [f"- {o['name']}: {o['days']} day(s), ${o['price_usd']:.2f}, {o['carbon_kg']} kg CO2e" for o in options]
    if rules.get("cutoff_time"):
        lines.append(f"Order before {rules['cutoff_time']} for same-day dispatch. We deliver in: {', '.join(rules.get('regions', []))}.")
    return lines

def _policy() -> List[str]:
    policy = ops.return_policy()
    return [f"Returns accepted within {policy['window_days']} days if the item is {' and '.join(policy['conditions'])}. Refund goes to the {policy['refund_method']} payment method."]

def _stores() -> List[str]:
    return [f"- {s['name']}: {s['address']} ({s.get('opening_hours', '')})" for s in store.rows("stores", "store_id") if s.get("active", True)]

def build(tenant: Dict[str, Any], topic: str) -> str:
    lines = [f"This is the store of {tenant['name']}. Prices are in US dollars."]
    if topic in ("shopping", "bidding"):
        lines += ["Products:"] + _products()
    if topic in ("delivery", "shopping"):
        lines += ["Delivery:"] + _delivery()
    if topic in ("support", "account and login", "shopping"):
        lines += ["Returns:"] + _policy()
    lines += ["Stores:"] + _stores()
    return "\n".join(lines)
