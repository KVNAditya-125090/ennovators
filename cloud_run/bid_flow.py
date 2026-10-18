"""
Cloud Run - AI bidding: counter-offer, hand-off and the consumer's decision
A shopper bargains with the AI bot (customer_handlers.py: start and customer-reply). This module holds the rest of the
flow, in the order it happens:

  counter-offer/send   the bot (or staff on its behalf) sends the shopper a lower counter-offer. It must stay at or above
                       the product's bidding floor, below the bot's last counter and above the shopper's last offer, and
                       the bot gives up bargaining after the number of counters the consumer allows (AI limits, 5 by default).
  finalize/handoff     a price both sides agreed is handed to the consumer. Customer-reply calls this on its own the
                       moment the shopper accepts or the offer reaches the floor; the endpoint is the same step done by hand.
                       The consumer's root gets a mail naming the bid, and the deal waits for a decision.
  pending/list         staff see the deals handed over (waiting by default, or confirmed, rejected or all), newest first,
                       each with its bid id, shopper, product and agreed price, ready for decision/accept or /reject.
  decision/accept      staff confirm the deal at the agreed price. decision/reject: staff refuse it, with a reason.

Bid statuses: open, accepted (price agreed, waiting for the consumer), confirmed (consumer accepted), declined (shopper
walked away), rejected (consumer refused). Bids live in the shopper's own record; a per-consumer index (bid id -> shopper)
lets staff reach them. Nothing here moves money or stock: a confirmed deal is a record the consumer acts on.
"""

import datetime
from typing import Any, Callable, Dict, Tuple

from firestore import store
from firestore.users.consumer import operations as ops
from cloud_run import rules


def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _index(tenant_id: str) -> Dict[str, str]:
    return store.kdoc("bid_index", "all", lambda: {"bids": {}}, tenant_id=tenant_id)["bids"]


def register(tenant: Dict[str, Any], bid_id: str, shopper_email: str) -> None:
    """Called when a bid is opened, so staff can find it by its id."""
    _index(tenant["tenant_id"])[bid_id] = shopper_email


def _find(tenant: Dict[str, Any], bid_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    email = _index(tenant["tenant_id"]).get(bid_id)
    if not email:
        raise LookupError(f"No bid {bid_id}")
    shopper = store.kdoc("shoppers", email, dict, tenant_id=tenant["tenant_id"])
    bid = next((b for b in shopper.get("bids", []) if b.get("bid_id") == bid_id), None)
    if bid is None:
        raise LookupError(f"No bid {bid_id}")
    return shopper, bid


def _floor(tenant: Dict[str, Any], bid: Dict[str, Any]) -> float:
    """The lowest price the bot may agree: the product's bidding floor, raised by the consumer's AI limits."""
    product = next((p for p in ops.list_products() if p["id"] == bid["product_id"]), None)
    if product is None:
        raise LookupError("The product of this bid is no longer listed.")
    return rules.effective_floor(tenant["tenant_id"], product)


def _shopper_last(bid: Dict[str, Any]) -> float:
    return next((float(r["price"]) for r in reversed(bid["rounds"]) if r["by"] != "seller"), float(bid["offer_price"]))


def _need_ai_bid(bid: Dict[str, Any]) -> None:
    if bid.get("mode") != "ai":
        raise ValueError("This is a bid between the shopper and your staff, not an AI-assisted bid.")


def counter_offer(tenant, params):
    _, bid = _find(tenant, params["bid_id"])
    _need_ai_bid(bid)
    if bid["status"] != "open":
        raise ValueError(f"This bid is already {bid['status']}, so no counter-offer can be sent.")
    if rules.expired(tenant["tenant_id"], bid):
        raise ValueError("This bid's window has closed.")
    price = round(float(params["price"]), 2)
    floor, last, asked = _floor(tenant, bid), float(bid["seller_counter"]), _shopper_last(bid)
    if price < floor:
        raise ValueError(f"A counter-offer cannot go below the bidding floor (${floor:.2f}).")
    if price >= last:
        raise ValueError(f"A counter-offer must be lower than the bot's last counter (${last:.2f}).")
    if price <= asked:
        raise ValueError(f"The shopper already offered ${asked:.2f}. Hand the deal over at that price instead.")
    limit = rules.ai_limits(tenant["tenant_id"])["max_rounds"]
    if sum(1 for r in bid["rounds"] if r["by"] == "seller") > limit:
        raise ValueError(f"The bot has already made {limit} counters. Hand the deal over or let it close.")
    bid["seller_counter"] = price
    bid["rounds"].append({"by": "seller", "price": price, "at": _now()})
    bid["bot_message"] = (params.get("message") or "").strip()[:300] or (f"${price:.2f} is my best price." if price == floor else f"I can do ${price:.2f}.")
    return {"status": bid["status"], "bid": bid}


def hand_off(tenant: Dict[str, Any], bid: Dict[str, Any], final_price: float, source: str) -> Dict[str, Any]:
    """The agreed price goes to the consumer. Used by the endpoint and by customer-reply."""
    final = round(float(final_price), 2)
    if bid.get("handoff"):
        raise ValueError("This deal was already handed to the consumer.")
    if bid["status"] not in ("open", "accepted"):
        raise ValueError(f"This bid is already {bid['status']}, so it cannot be handed over.")
    floor = _floor(tenant, bid)
    if final < floor:
        raise ValueError(f"The final price cannot be below the bidding floor (${floor:.2f}).")
    bid["status"], bid["agreed_price"] = "accepted", final
    bid["handoff"] = {"status": "pending", "price": final, "at": _now(), "source": source}
    bid["bot_message"] = f"Deal at ${final:.2f}. The seller will confirm it shortly."
    ops.send_root_mail(tenant["tenant_id"], "bid_handoff", None, f"AI bid {bid['bid_id']} on {bid['name']} agreed at ${final:.2f} and waits for your decision.")
    return bid


def finalize(tenant, params):
    _, bid = _find(tenant, params["bid_id"])
    _need_ai_bid(bid)
    hand_off(tenant, bid, params["final_price"], "AI")
    return {"status": bid["status"], "bid": bid}


def _decide(tenant, params, accept: bool):
    _, bid = _find(tenant, params["bid_id"])
    _need_ai_bid(bid)
    handoff = bid.get("handoff")
    if not handoff:
        raise ValueError("This deal has not been handed to the consumer yet.")
    if handoff["status"] != "pending":
        raise ValueError(f"This deal was already {handoff['status']}.")
    who = ops.ACTOR.get() or ""
    if accept:
        handoff.update({"status": "confirmed", "decided_at": _now(), "decided_by": who})
        bid["status"] = "confirmed"
        bid["bot_message"] = f"Confirmed: ${bid['agreed_price']:.2f}."
    else:
        reason = (params.get("reason") or "").strip()[:300]
        handoff.update({"status": "rejected", "decided_at": _now(), "decided_by": who, "reason": reason})
        bid["status"] = "rejected"
        bid["bot_message"] = "The seller could not confirm this price." + (f" {reason}" if reason else "")
    return {"status": bid["status"], "bid": bid}


def accept(tenant, params):
    return _decide(tenant, params, True)


def reject(tenant, params):
    return _decide(tenant, params, False)


def pending_list(tenant, params):
    wanted = params.get("status") or "pending"
    if wanted not in ("pending", "confirmed", "rejected", "all"):
        raise ValueError("Status must be pending, confirmed, rejected or all.")
    tid = tenant["tenant_id"]
    items = []
    for bid_id, email in _index(tid).items():
        shopper = store.kdoc("shoppers", email, dict, tenant_id=tid)
        bid = next((b for b in shopper.get("bids", []) if b.get("bid_id") == bid_id), None)
        handoff = (bid or {}).get("handoff")
        if not handoff or (wanted != "all" and handoff["status"] != wanted):
            continue
        items.append({"bid_id": bid_id, "decision": handoff["status"], "product_id": bid["product_id"], "product": bid["name"],
                      "shopper": (shopper.get("profile") or {}).get("full_name") or email, "shopper_email": email,
                      "shopper_first_offer": bid["offer_price"], "agreed_price": handoff["price"], "bidding_floor": _floor(tenant, bid),
                      "rounds": len(bid["rounds"]), "handed_over_at": handoff["at"], "handed_over_by": handoff["source"],
                      "decided_at": handoff.get("decided_at"), "decided_by": handoff.get("decided_by"), "reason": handoff.get("reason")})
    items.sort(key=lambda i: i["handed_over_at"], reverse=True)
    return {"status": wanted, "count": len(items), "deals": items}


def install(handlers: Dict[str, Callable]) -> int:
    table = {"/paas/bid/ai/counter-offer/send/v1": counter_offer, "/paas/bid/ai/finalize/handoff/v1": finalize,
             "/paas/bid/ai/pending/list/v1": pending_list, "/paas/bid/ai/decision/accept/v1": accept, "/paas/bid/ai/decision/reject/v1": reject}
    handlers.update(table)
    return len(table)
