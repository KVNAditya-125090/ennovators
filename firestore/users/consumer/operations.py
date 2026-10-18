"""
Firestore - Consumer operations
What a Consumer's business does day to day, in memory for the preview: products and stock, orders, shipments,
support tickets, returns, internal roles and company settings. Each function is one catalog endpoint.
A missing record raises LookupError and a refused change raises ValueError; the gate turns them into 404 and 422.
"""

import itertools
import re
import contextvars
from typing import Any, Dict, List, Optional
from firestore.services.paas import firestore_paas
from firestore.services.taas import firestore_taas
from cloud_run.ids import new_id
from firestore import store
from cloud_sql.services.maas.roles import roles as role_store
from cloud_sql.services.maas.mailflows import mail_flows

_ids = itertools.count(1)
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

def _next(prefix: str = "") -> str:
    """A new record id: a UUID (the prefix is ignored, kept so callers read the same)."""
    return new_id()

def _find(rows: List[Dict[str, Any]], key: str, value: Any) -> Dict[str, Any]:
    row = next((r for r in rows if r[key] == value), None)
    if row is None:
        raise LookupError(f"No record with {key} {value}")
    return row

# ---- PaaS: products, stock, orders ----
PLACEHOLDER_IMAGE = ""
CONDITIONS = {"new": "New / Factory Sealed", "refurbished": "Certified Refurbished", "used": "Used"}

def condition_key(text: str) -> str:
    """The allowed value (new, refurbished or used) that a product's condition text belongs to, or "" when it matches none."""
    t = (text or "").lower()
    return "refurbished" if "refurb" in t else "used" if "used" in t else "new" if "new" in t else ""

def list_products() -> List[Dict[str, Any]]:
    return [p for p in firestore_paas.list_products() if not p.get("archived")]

def _price(value: Any) -> float:
    price = float(value)
    if price < 0:
        raise ValueError("Price cannot be negative")
    return price

MEDIA_PREFIX = "/api/v1/media/"

def _media(urls: Any, what: str) -> List[str]:
    """Keeps the pictures or videos of a product: addresses of files uploaded here, or web addresses. Nothing else."""
    out = []
    for u in urls or []:
        u = str(u).strip()
        if not (u.startswith(MEDIA_PREFIX) or u.startswith("https://") or u.startswith("http://")):
            raise ValueError(f"Each {what} must be an uploaded file or a web address")
        out.append(u)
    if len(out) > 10:
        raise ValueError(f"A product can have up to 10 {what}s")
    return out

def create_product(p: Dict[str, Any]) -> Dict[str, Any]:
    price = _price(p["price"])
    if int(p.get("stock") or 0) < 0:
        raise ValueError("Stock cannot be negative")
    if any(x["sku"] == p["sku"] for x in firestore_paas.list_products()):
        raise ValueError(f"SKU {p['sku']} already exists")
    product = {"id": _next("prod"), "name": p["name"], "sku": p["sku"], "category": str(p["category_id"]),
               "description": p.get("description", ""), "retail_price": price,
               "current_bidding_floor": round(price * 0.72, 2),
               "condition": CONDITIONS.get(p.get("condition", "new"), "New / Factory Sealed"),
               "stock": int(p.get("stock") or 0), "carbon_footprint_kg": 0}
    product["images"] = _media(p.get("images"), "picture")
    product["videos"] = _media(p.get("videos"), "video")
    product["image_url"] = (product["images"] or [PLACEHOLDER_IMAGE])[0]
    firestore_paas.list_products().append(product)
    return product

def update_product(p: Dict[str, Any]) -> Dict[str, Any]:
    product = _find(firestore_paas.list_products(), "id", p["product_id"])
    for src, dst in (("name", "name"), ("description", "description"), ("category_id", "category"), ("price", "retail_price")):
        if p.get(src) not in (None, ""):
            product[dst] = _price(p[src]) if dst == "retail_price" else p[src]
    # a product's condition can carry detail the three choices do not (such as "Certified Refurbished (Grade A)"): keep it unless the family changed
    if p.get("condition") and condition_key(product.get("condition", "")) != p["condition"]:
        product["condition"] = CONDITIONS[p["condition"]]
    if "images" in p:  # a list, even an empty one, replaces what the product had
        product["images"] = _media(p["images"], "picture")
        product["image_url"] = (product["images"] or [PLACEHOLDER_IMAGE])[0]
    if "videos" in p:
        product["videos"] = _media(p["videos"], "video")
    return product

def archive_product(product_id: str) -> Dict[str, Any]:
    product = _find(firestore_paas.list_products(), "id", product_id)
    product["archived"] = True
    return product

def _by_sku(sku: str) -> Dict[str, Any]:
    return _find(firestore_paas.list_products(), "sku", sku)

def read_stock(sku: Optional[str]) -> List[Dict[str, Any]]:
    return [{"sku": p["sku"], "name": p["name"], "quantity": p["stock"]} for p in list_products() if not sku or p["sku"] == sku]

def update_stock(sku: str, quantity: int) -> Dict[str, Any]:
    if quantity < 0:
        raise ValueError("Stock cannot be negative")
    _by_sku(sku)["stock"] = quantity
    return {"sku": sku, "quantity": quantity}

def adjust_stock(sku: str, change: int, reason: str) -> Dict[str, Any]:
    product = _by_sku(sku)
    if product["stock"] + change < 0:
        raise ValueError("The adjustment would take stock below zero")
    product["stock"] += change
    return {"sku": sku, "quantity": product["stock"], "reason": reason}

def _orders() -> List[Dict[str, Any]]:
    return store.rows("orders", "order_id", newest_first=True)

def read_orders(status: Optional[str]) -> List[Dict[str, Any]]:
    return [o for o in _orders() if not status or o["status"] == status]

# An order only moves forward; delivered and cancelled orders are final.
ORDER_FLOW = {"placed": {"paid", "cancelled"}, "paid": {"shipped", "cancelled"}, "shipped": {"delivered"}, "delivered": set(), "cancelled": set()}

def update_order_status(order_id: str, status: str) -> Dict[str, Any]:
    order = _find(_orders(), "order_id", order_id)
    if status == order["status"]:
        return order
    if status not in ORDER_FLOW.get(order["status"], set()):
        raise ValueError(f"An order that is {order['status']} cannot be marked {status}")
    order["status"] = status
    return order

# ---- TaaS: shipments ----
def list_shipments(status: Optional[str]) -> List[Dict[str, Any]]:
    return [s for s in firestore_taas.list_shipments() if not status or s["status"] == status]

def create_shipment(order_id: str, carrier: Optional[str]) -> Dict[str, Any]:
    order = _find(_orders(), "order_id", order_id)
    shipment = {"shipment_id": _next("shp"), "order_id": order_id, "type": "Forward Delivery", "origin": "",
                "destination": order["customer"], "status": "created", "carrier": carrier or "",
                "eta": "", "co2_saved_kg": 0, "events": [{"at": _now(), "event": "Shipment created"}]}
    firestore_taas.list_shipments().append(shipment)
    return shipment

def update_shipment_status(shipment_id: str, status: str) -> Dict[str, Any]:
    shipment = _find(firestore_taas.list_shipments(), "shipment_id", shipment_id)
    shipment["status"] = status
    shipment.setdefault("events", []).append({"at": _now(), "event": "Status: " + status.replace("_", " ")})
    return shipment

def cancel_shipment(shipment_id: str, reason: Optional[str]) -> Dict[str, Any]:
    shipment = _find(firestore_taas.list_shipments(), "shipment_id", shipment_id)
    if shipment["status"] == "delivered":
        raise ValueError("A delivered shipment cannot be cancelled")
    shipment["status"] = "cancelled"
    shipment["cancel_reason"] = reason or ""
    shipment.setdefault("events", []).append({"at": _now(), "event": "Cancelled"})
    return shipment

# ---- SaaS: tickets and returns ----
def _tickets() -> List[Dict[str, Any]]:
    return store.rows("tickets", "ticket_id", newest_first=True)

def read_tickets(status: Optional[str]) -> List[Dict[str, Any]]:
    return [t for t in _tickets() if not status or t["status"] == status]

def reply_ticket(ticket_id: str, message: str, author: Optional[str] = None) -> Dict[str, Any]:
    ticket = _find(_tickets(), "ticket_id", ticket_id)
    if ticket["status"] == "closed":
        raise ValueError("This ticket is closed")
    ticket["messages"].append({"from": "Staff", "author": author, "text": message, "at": _now()})
    if ticket["status"] == "open":
        ticket["status"] = "in_progress"
    return ticket

def update_ticket_status(ticket_id: str, status: str) -> Dict[str, Any]:
    ticket = _find(_tickets(), "ticket_id", ticket_id)
    ticket["status"] = status
    return ticket

def close_ticket(ticket_id: str, resolution: Optional[str]) -> Dict[str, Any]:
    ticket = _find(_tickets(), "ticket_id", ticket_id)
    ticket["status"] = "closed"
    if resolution:
        ticket["messages"].append({"from": "Staff", "text": f"Resolution: {resolution}", "at": _now()})
    return ticket

def _returns() -> List[Dict[str, Any]]:
    return store.rows("returns", "return_id", newest_first=True)
def return_policy() -> Dict[str, Any]:
    return store.kdoc("config", "return_policy", lambda: {"window_days": 30, "conditions": ["unused", "original packaging"], "refund_method": "original"})

def read_returns(status: Optional[str]) -> List[Dict[str, Any]]:
    return [r for r in _returns() if not status or r["status"] == status]

def _move_return(return_id: str, expect: str, to: str) -> Dict[str, Any]:
    ret = _find(_returns(), "return_id", return_id)
    if ret["status"] != expect:
        raise ValueError(f"This return is {ret['status']}; only a {expect} return can move to {to}")
    ret["status"] = to
    return ret

def approve_return(return_id: str) -> Dict[str, Any]:
    return _move_return(return_id, "requested", "approved")

def reject_return(return_id: str, reason: str) -> Dict[str, Any]:
    ret = _move_return(return_id, "requested", "rejected")
    ret["reject_reason"] = reason
    return ret

def issue_refund(return_id: str, amount: float) -> Dict[str, Any]:
    ret = _find(_returns(), "return_id", return_id)
    if amount > ret["amount"]:
        raise ValueError("The refund cannot be more than the item's price")
    ret = _move_return(return_id, "approved", "refunded")
    ret["refunded"] = amount
    return ret

def set_return_policy(window_days: int, conditions: Optional[list], refund_method: str) -> Dict[str, Any]:
    policy = return_policy()
    policy.update({"window_days": window_days, "refund_method": refund_method, **({"conditions": conditions} if conditions else {})})
    return policy

# ---- MaaS: internal roles and company settings ----
def settings() -> Dict[str, Any]:
    return store.kdoc("config", "settings", lambda: {"company_name": "", "contact_mail": "", "timezone": "", "default_language": "", "default_currency": ""})

def list_roles(tenant_id: str) -> List[Dict[str, Any]]:
    return role_store.list_roles(tenant_id)

def create_role(tenant_id: str, name: str, description: Optional[str]) -> Dict[str, Any]:
    role = role_store.create_role(tenant_id, name, description)
    send_root_mail(tenant_id, "role-created", role["role_id"], f"The {name} role was created.")
    return role

def update_role(tenant_id: str, role_id: str, name: Optional[str], description: Optional[str]) -> Dict[str, Any]:
    return role_store.update_role(tenant_id, role_id, name, description)

def deactivate_role(tenant_id: str, role_id: str) -> Dict[str, Any]:
    role = role_store.deactivate_role(tenant_id, role_id)
    send_root_mail(tenant_id, "role-deactivated", role_id, f"The {role['name']} role was deactivated.")
    return role

def update_settings(values: Dict[str, Any]) -> Dict[str, Any]:
    current = settings()
    current.update({k: v for k, v in values.items() if k in current and v not in (None, "")})
    return current

# ---- MaaS: who holds each role, what each role may do, and the mails sent to the root ----
# ---- MaaS: who holds each role, what each role may do, and the mails sent to the root (kept in Cloud SQL, per consumer) ----
# Who is making the current call. The gate sets it, so the log can say who did each thing.
ACTOR: contextvars.ContextVar = contextvars.ContextVar("actor", default=None)
# The signed-in shopper making the current call (their email), set by the gate for Customer-side endpoints.
# A customer has a separate account with each consumer, so their data is kept per (consumer, customer).
CUSTOMER: contextvars.ContextVar = contextvars.ContextVar("customer", default=None)

def _now() -> str:
    import datetime
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")

def send_root_mail(tenant_id: str, event_type: str, role_id: Optional[str], message: str) -> None:
    """The root gets a mail for every internal-role event."""
    role_store.log_mail(tenant_id, event_type, role_id, ACTOR.get(), message)

def read_mail_log(tenant_id: str) -> List[Dict[str, Any]]:
    return role_store.mail_log(tenant_id)

def list_role_mails(tenant_id: str) -> List[Dict[str, Any]]:
    return role_store.list_mails(tenant_id)

def assign_role_mail(tenant_id: str, role_id: str, mail: str) -> Dict[str, Any]:
    entry = role_store.assign_mail(tenant_id, role_id, mail)
    name = role_store.get_role(tenant_id, role_id)["name"]
    send_root_mail(tenant_id, "role-mail-assigned", role_id, f"{entry['mail']} was given the {name} role. A sign-in invite was sent to them.")
    mail_flows.send_invite(tenant_id, role_id, entry["mail"], ACTOR.get())
    return entry

def remove_role_mail(tenant_id: str, role_id: str, mail: str) -> Dict[str, Any]:
    entry = role_store.remove_mail(tenant_id, role_id, mail)
    name = role_store.get_role(tenant_id, role_id)["name"]
    send_root_mail(tenant_id, "role-mail-removed", role_id, f"{entry['mail']} no longer has access to the {name} role.")
    return entry

def read_role_permissions(tenant_id: str, role_id: str) -> List[str]:
    return role_store.permissions(tenant_id, role_id)

def assign_role_permission(tenant_id: str, role_id: str, path: str) -> Dict[str, Any]:
    role_store.grant(tenant_id, role_id, path)
    name = role_store.get_role(tenant_id, role_id)["name"]
    send_root_mail(tenant_id, "role-permission-granted", role_id, f"The {name} role can now use {path}.")
    return {"role_id": role_id, "endpoint_path": path}

def revoke_role_permission(tenant_id: str, role_id: str, path: str) -> Dict[str, Any]:
    role_store.revoke(tenant_id, role_id, path)
    name = role_store.get_role(tenant_id, role_id)["name"]
    send_root_mail(tenant_id, "role-permission-revoked", role_id, f"The {name} role can no longer use {path}.")
    return {"role_id": role_id, "endpoint_path": path}


# ---- TaaS: routing returns, delivery rules and the delivery picture ----
RETURN_ROUTES = ("resale", "refurbish", "donate", "parts", "recycle")

def route_return(return_id: str, kind: str) -> Dict[str, Any]:
    ret = _find(_returns(), "return_id", return_id)
    if ret["status"] not in ("approved", "refunded"):
        raise ValueError("Only an approved return can be routed")
    ret["route"] = kind
    return ret

def schedule_return_pickup(return_id: str, pickup_at: str, carrier: Optional[str]) -> Dict[str, Any]:
    ret = _find(_returns(), "return_id", return_id)
    if ret["status"] not in ("approved", "refunded"):
        raise ValueError("Only an approved return can be collected")
    ret["pickup"] = {"at": pickup_at, "carrier": carrier or ""}
    return ret

def delivery_rules() -> Dict[str, Any]:
    return store.kdoc("config", "delivery_rules", lambda: {"options": [], "cutoff_time": "", "regions": []})

def service_area() -> Dict[str, Any]:
    return store.kdoc("config", "service_area", lambda: {"mode": "", "regions": []})

def set_delivery_rules(options: list, cutoff_time: Optional[str], regions: Optional[list]) -> Dict[str, Any]:
    if not options:
        raise ValueError("Offer at least one delivery option")
    rules = delivery_rules()
    rules.update({"options": options, "cutoff_time": cutoff_time or rules["cutoff_time"], **({"regions": regions} if regions else {})})
    return rules

def set_service_area(mode: str, regions: list) -> Dict[str, Any]:
    if mode == "local" and not regions:
        raise ValueError("Name the regions you deliver to")
    area = service_area()
    area.update({"mode": mode, "regions": regions})
    return area

# ---- MaaS: the template, how roles see their workspace, and the customer storefront (kept in Cloud SQL, per consumer) ----
def _template(tenant_id: str) -> Dict[str, Any]:
    t = role_store.get_template(tenant_id)
    if not t:
        raise LookupError("No template yet")
    return t

def read_template(tenant_id: str) -> Dict[str, Any]:
    return role_store.get_template(tenant_id) or {"exists": False, "role_views": {}}

def create_template(tenant_id: str, name: str, layout: Dict[str, Any], branding: Optional[Dict[str, Any]], sections: Optional[list]) -> Dict[str, Any]:
    if role_store.get_template(tenant_id):
        raise ValueError("A template already exists. Edit it instead.")
    return role_store.save_template(tenant_id, {"exists": True, "name": name, "layout": layout, "branding": branding or {}, "sections": sections or [],
                                                "role_views": {}, "version": 0, "published": False, "published_at": None, "version_note": ""})

def update_template(tenant_id: str, layout: Optional[Dict[str, Any]], branding: Optional[Dict[str, Any]], sections: Optional[list]) -> Dict[str, Any]:
    t = _template(tenant_id)
    if layout is not None:
        t["layout"] = layout
    if branding is not None:
        t["branding"] = branding
    if sections is not None:
        t["sections"] = sections
    t["published"] = False if t["version"] == 0 else t["published"]
    t["unpublished_changes"] = True
    return role_store.save_template(tenant_id, t)

def set_role_view(tenant_id: str, role_id: str, view: Dict[str, Any]) -> Dict[str, Any]:
    t = role_store.get_template(tenant_id)
    if not t:
        t = create_template(tenant_id, "Customer storefront", {"style": "grid", "hero": True}, {"colour": "#1A73E8"}, [])
    role_store.get_role(tenant_id, role_id)
    t["role_views"][role_id] = view
    return role_store.save_template(tenant_id, t)

def publish_template(tenant_id: str, note: Optional[str]) -> Dict[str, Any]:
    t = _template(tenant_id)
    t.update({"version": t["version"] + 1, "published": True, "published_at": _now(), "version_note": note or "", "unpublished_changes": False})
    role_store.save_template(tenant_id, t)
    send_root_mail(tenant_id, "template-published", None, f"The customer storefront was published as version {t['version']}.")
    return t
