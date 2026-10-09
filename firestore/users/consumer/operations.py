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

_ids = itertools.count(1)
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

def _next(prefix: str) -> str:
    return f"{prefix}-{next(_ids) + 1000}"

def _find(rows: List[Dict[str, Any]], key: str, value: Any) -> Dict[str, Any]:
    row = next((r for r in rows if r[key] == value), None)
    if row is None:
        raise LookupError(f"No record with {key} {value}")
    return row

# ---- PaaS: products, stock, orders ----
PLACEHOLDER_IMAGE = "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop"
CONDITIONS = {"new": "New / Factory Sealed", "refurbished": "Certified Refurbished", "used": "Used"}

def list_products() -> List[Dict[str, Any]]:
    return [p for p in firestore_paas.list_products() if not p.get("archived")]

def _price(value: Any) -> float:
    price = float(value)
    if price < 0:
        raise ValueError("Price cannot be negative")
    return price

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
               "stock": int(p.get("stock") or 0), "image_url": (p.get("images") or [PLACEHOLDER_IMAGE])[0], "carbon_footprint_kg": 0}
    firestore_paas.list_products().append(product)
    return product

def update_product(p: Dict[str, Any]) -> Dict[str, Any]:
    product = _find(firestore_paas.list_products(), "id", p["product_id"])
    for src, dst in (("name", "name"), ("description", "description"), ("category_id", "category"), ("price", "retail_price")):
        if p.get(src) not in (None, ""):
            product[dst] = _price(p[src]) if dst == "retail_price" else p[src]
    if p.get("condition"):
        product["condition"] = CONDITIONS[p["condition"]]
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

ORDERS: List[Dict[str, Any]] = [
    {"order_id": "ord-5001", "customer": "Marcus Vance", "items": "Aura Smart Eco Watch (Gen 3) x1", "total": 249.99, "status": "paid", "placed": "2026-10-06"},
    {"order_id": "ord-5002", "customer": "Ananya Rao", "items": "Circular Noise-Canceling Headphones x2", "total": 398.00, "status": "placed", "placed": "2026-10-07"},
    {"order_id": "ord-5003", "customer": "Devika Shah", "items": "Modular Solar Power Bank x1", "total": 89.50, "status": "shipped", "placed": "2026-10-04"},
    {"order_id": "ord-5004", "customer": "Karan Mehta", "items": "Aura Smart Eco Watch (Gen 3) x1", "total": 249.99, "status": "delivered", "placed": "2026-09-29"},
]

def read_orders(status: Optional[str]) -> List[Dict[str, Any]]:
    return [o for o in ORDERS if not status or o["status"] == status]

# An order only moves forward; delivered and cancelled orders are final.
ORDER_FLOW = {"placed": {"paid", "cancelled"}, "paid": {"shipped", "cancelled"}, "shipped": {"delivered"}, "delivered": set(), "cancelled": set()}

def update_order_status(order_id: str, status: str) -> Dict[str, Any]:
    order = _find(ORDERS, "order_id", order_id)
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
    order = _find(ORDERS, "order_id", order_id)
    shipment = {"shipment_id": _next("shp"), "order_id": order_id, "type": "Forward Delivery", "origin": "Central Warehouse (Bengaluru)",
                "destination": order["customer"], "status": "created", "carrier": carrier or "EcoExpress Zero-Emission Electric",
                "eta": "In 3 days", "co2_saved_kg": 1.5}
    firestore_taas.list_shipments().append(shipment)
    return shipment

def update_shipment_status(shipment_id: str, status: str) -> Dict[str, Any]:
    shipment = _find(firestore_taas.list_shipments(), "shipment_id", shipment_id)
    shipment["status"] = status
    return shipment

def cancel_shipment(shipment_id: str, reason: Optional[str]) -> Dict[str, Any]:
    shipment = _find(firestore_taas.list_shipments(), "shipment_id", shipment_id)
    if shipment["status"] == "delivered":
        raise ValueError("A delivered shipment cannot be cancelled")
    shipment["status"] = "cancelled"
    shipment["cancel_reason"] = reason or ""
    return shipment

# ---- SaaS: tickets and returns ----
TICKETS: List[Dict[str, Any]] = [
    {"ticket_id": "tkt-7001", "customer": "Marcus Vance", "subject": "Watch will not charge", "status": "open",
     "messages": [{"from": "Customer", "text": "My watch stopped charging after two days."}]},
    {"ticket_id": "tkt-7002", "customer": "Ananya Rao", "subject": "Wrong colour delivered", "status": "in_progress",
     "messages": [{"from": "Customer", "text": "I ordered black headphones but received white."}, {"from": "Staff", "author": "Priya Nair", "text": "Sorry about that, we are checking stock."}]},
    {"ticket_id": "tkt-7003", "customer": "Devika Shah", "subject": "Invoice copy", "status": "resolved",
     "messages": [{"from": "Customer", "text": "Please resend my invoice."}, {"from": "Staff", "author": "Priya Nair", "text": "Sent to your mail."}]},
]

def read_tickets(status: Optional[str]) -> List[Dict[str, Any]]:
    return [t for t in TICKETS if not status or t["status"] == status]

def reply_ticket(ticket_id: str, message: str, author: Optional[str] = None) -> Dict[str, Any]:
    ticket = _find(TICKETS, "ticket_id", ticket_id)
    if ticket["status"] == "closed":
        raise ValueError("This ticket is closed")
    ticket["messages"].append({"from": "Staff", "author": author, "text": message})
    if ticket["status"] == "open":
        ticket["status"] = "in_progress"
    return ticket

def update_ticket_status(ticket_id: str, status: str) -> Dict[str, Any]:
    ticket = _find(TICKETS, "ticket_id", ticket_id)
    ticket["status"] = status
    return ticket

def close_ticket(ticket_id: str, resolution: Optional[str]) -> Dict[str, Any]:
    ticket = _find(TICKETS, "ticket_id", ticket_id)
    ticket["status"] = "closed"
    if resolution:
        ticket["messages"].append({"from": "Staff", "text": f"Resolution: {resolution}"})
    return ticket

RETURNS: List[Dict[str, Any]] = [
    {"return_id": "ret-8001", "order_id": "ord-5004", "customer": "Karan Mehta", "item": "Aura Smart Eco Watch (Gen 3)", "reason": "Strap too small", "amount": 249.99, "status": "requested"},
    {"return_id": "ret-8002", "order_id": "ord-5003", "customer": "Devika Shah", "item": "Modular Solar Power Bank", "reason": "Does not hold charge", "amount": 89.50, "status": "approved"},
]
RETURN_POLICY: Dict[str, Any] = {"window_days": 30, "conditions": ["unused", "original packaging"], "refund_method": "original"}

def read_returns(status: Optional[str]) -> List[Dict[str, Any]]:
    return [r for r in RETURNS if not status or r["status"] == status]

def _move_return(return_id: str, expect: str, to: str) -> Dict[str, Any]:
    ret = _find(RETURNS, "return_id", return_id)
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
    ret = _find(RETURNS, "return_id", return_id)
    if amount > ret["amount"]:
        raise ValueError("The refund cannot be more than the item's price")
    ret = _move_return(return_id, "approved", "refunded")
    ret["refunded"] = amount
    return ret

def set_return_policy(window_days: int, conditions: Optional[list], refund_method: str) -> Dict[str, Any]:
    RETURN_POLICY.update({"window_days": window_days, "refund_method": refund_method, **({"conditions": conditions} if conditions else {})})
    return RETURN_POLICY

# ---- MaaS: internal roles and company settings ----
ROLES: List[Dict[str, Any]] = [
    {"role_id": "role-1", "name": "Manager", "description": "Runs the workspace", "active": True},
    {"role_id": "role-2", "name": "Seller", "description": "Lists and sells products", "active": True},
    {"role_id": "role-3", "name": "Dispatcher", "description": "Moves goods", "active": True},
]
SETTINGS: Dict[str, Any] = {"company_name": "GreenCycle Refurbishers LLP", "contact_mail": "sarah.chen@greencycle.example",
                            "timezone": "IST (UTC+5:30)", "default_language": "English", "default_currency": "USD"}

def create_role(name: str, description: Optional[str]) -> Dict[str, Any]:
    if any(r["name"].lower() == name.lower() for r in ROLES):
        raise ValueError(f"A role called {name} already exists")
    role = {"role_id": _next("role"), "name": name, "description": description or "", "active": True}
    ROLES.append(role)
    send_root_mail("role-created", role["role_id"], f"The {name} role was created.")
    return role

def update_role(role_id: str, name: Optional[str], description: Optional[str]) -> Dict[str, Any]:
    role = _find(ROLES, "role_id", role_id)
    if name:
        role["name"] = name
    if description is not None:
        role["description"] = description
    return role

def deactivate_role(role_id: str) -> Dict[str, Any]:
    role = _find(ROLES, "role_id", role_id)
    role["active"] = False
    send_root_mail("role-deactivated", role_id, f"The {role['name']} role was deactivated.")
    return role

def update_settings(values: Dict[str, Any]) -> Dict[str, Any]:
    SETTINGS.update({k: v for k, v in values.items() if k in SETTINGS and v not in (None, "")})
    return SETTINGS

# ---- MaaS: who holds each role, what each role may do, and the mails sent to the root ----
ROLE_MAILS: List[Dict[str, Any]] = [
    {"role_id": "role-1", "mail": "rahul@greencycle.com", "status": "active"},
    {"role_id": "role-2", "mail": "anika@greencycle.com", "status": "active"},
    {"role_id": "role-3", "mail": "priya@greencycle.com", "status": "active"},
]
ROLE_PERMISSIONS: Dict[str, set] = {
    "role-1": {"/paas/order/read/staff/v1", "/paas/order/status/update/v1", "/taas/shipment/read/staff/v1"},
    "role-2": {"/paas/catalog/product/read/v1", "/paas/catalog/product/create/v1", "/paas/catalog/product/update/v1"},
    "role-3": {"/taas/shipment/read/staff/v1", "/taas/shipment/status/update/v1", "/taas/shipment/create/v1",
               # AI delivery planning: dispatchers plan each shipment and accept or override the AI
               "/taas/route/optimize/recommend/v1", "/taas/vehicle/recommend/v1", "/taas/delivery/eta/predict/v1",
               "/taas/delivery/slot/recommend/v1", "/taas/explain/decision/read/v1", "/taas/recommendation/accept/v1",
               "/taas/recommendation/override/v1"},
}
MAIL_LOG: List[Dict[str, Any]] = []
# Who is making the current call. The gate sets it, so the log can say who did each thing.
ACTOR: contextvars.ContextVar = contextvars.ContextVar("actor", default=None)

def _now() -> str:
    import datetime
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")

def send_root_mail(event_type: str, role_id: Optional[str], message: str) -> None:
    """The root gets a mail for every internal-role event."""
    MAIL_LOG.insert(0, {"at": _now(), "event_type": event_type, "role_id": role_id, "actor": ACTOR.get(), "message": message})

def read_mail_log() -> List[Dict[str, Any]]:
    return MAIL_LOG

def list_role_mails() -> List[Dict[str, Any]]:
    return ROLE_MAILS

def assign_role_mail(role_id: str, mail: str) -> Dict[str, Any]:
    role = _find(ROLES, "role_id", role_id)
    if not role["active"]:
        raise ValueError(f"The {role['name']} role is inactive")
    mail = mail.strip().lower()
    if not EMAIL.fullmatch(mail):
        raise ValueError(f"{mail} is not a valid email address")
    if any(m["mail"] == mail and m["role_id"] == role_id for m in ROLE_MAILS):
        raise ValueError(f"{mail} already holds the {role['name']} role")
    entry = {"role_id": role_id, "mail": mail, "status": "invited"}
    ROLE_MAILS.append(entry)
    send_root_mail("role-mail-assigned", role_id, f"{mail} was given the {role['name']} role. A sign-in invite was sent to them.")
    return entry

def remove_role_mail(role_id: str, mail: str) -> Dict[str, Any]:
    mail = mail.strip().lower()
    entry = next((m for m in ROLE_MAILS if m["role_id"] == role_id and m["mail"] == mail), None)
    if entry is None:
        raise LookupError(f"{mail} does not hold this role")
    ROLE_MAILS.remove(entry)
    send_root_mail("role-mail-removed", role_id, f"{mail} no longer has access to the {_find(ROLES, 'role_id', role_id)['name']} role.")
    return entry

def read_role_permissions(role_id: str) -> List[str]:
    _find(ROLES, "role_id", role_id)
    return sorted(ROLE_PERMISSIONS.get(role_id, set()))

def assign_role_permission(role_id: str, path: str) -> Dict[str, Any]:
    role = _find(ROLES, "role_id", role_id)
    if not role["active"]:
        raise ValueError(f"The {role['name']} role is inactive")
    ROLE_PERMISSIONS.setdefault(role_id, set()).add(path)
    send_root_mail("role-permission-granted", role_id, f"The {role['name']} role can now use {path}.")
    return {"role_id": role_id, "endpoint_path": path}

def revoke_role_permission(role_id: str, path: str) -> Dict[str, Any]:
    role = _find(ROLES, "role_id", role_id)
    ROLE_PERMISSIONS.setdefault(role_id, set()).discard(path)
    send_root_mail("role-permission-revoked", role_id, f"The {role['name']} role can no longer use {path}.")
    return {"role_id": role_id, "endpoint_path": path}


# ---- TaaS: routing returns, delivery rules and the delivery picture ----
RETURN_ROUTES = ("resale", "refurbish", "donate", "parts", "recycle")

def route_return(return_id: str, kind: str) -> Dict[str, Any]:
    ret = _find(RETURNS, "return_id", return_id)
    if ret["status"] not in ("approved", "refunded"):
        raise ValueError("Only an approved return can be routed")
    ret["route"] = kind
    return ret

def schedule_return_pickup(return_id: str, pickup_at: str, carrier: Optional[str]) -> Dict[str, Any]:
    ret = _find(RETURNS, "return_id", return_id)
    if ret["status"] not in ("approved", "refunded"):
        raise ValueError("Only an approved return can be collected")
    ret["pickup"] = {"at": pickup_at, "carrier": carrier or "Peer2Peer Green Relay"}
    return ret

DELIVERY_RULES: Dict[str, Any] = {"options": ["Standard (3-5 days)", "Express (1-2 days)", "Store pickup"], "cutoff_time": "16:00", "regions": ["Karnataka", "Maharashtra", "Telangana"]}
SERVICE_AREA: Dict[str, Any] = {"mode": "local", "regions": ["Karnataka", "Maharashtra", "Telangana"]}

def set_delivery_rules(options: list, cutoff_time: Optional[str], regions: Optional[list]) -> Dict[str, Any]:
    if not options:
        raise ValueError("Offer at least one delivery option")
    DELIVERY_RULES.update({"options": options, "cutoff_time": cutoff_time or DELIVERY_RULES["cutoff_time"], **({"regions": regions} if regions else {})})
    return DELIVERY_RULES

def set_service_area(mode: str, regions: list) -> Dict[str, Any]:
    if mode == "local" and not regions:
        raise ValueError("Name the regions you deliver to")
    SERVICE_AREA.update({"mode": mode, "regions": regions})
    return SERVICE_AREA

# ---- MaaS: the template, how roles see their workspace, and the customer storefront ----
TEMPLATE: Dict[str, Any] = {}

def _template() -> Dict[str, Any]:
    if not TEMPLATE:
        raise LookupError("No template yet")
    return TEMPLATE

def read_template() -> Dict[str, Any]:
    return TEMPLATE or {"exists": False, "role_views": {}}

def create_template(name: str, layout: Dict[str, Any], branding: Optional[Dict[str, Any]], sections: Optional[list]) -> Dict[str, Any]:
    if TEMPLATE:
        raise ValueError("A template already exists. Edit it instead.")
    TEMPLATE.update({"exists": True, "name": name, "layout": layout, "branding": branding or {}, "sections": sections or [], "role_views": {},
                     "version": 0, "published": False, "published_at": None, "version_note": ""})
    return TEMPLATE

def update_template(layout: Optional[Dict[str, Any]], branding: Optional[Dict[str, Any]], sections: Optional[list]) -> Dict[str, Any]:
    t = _template()
    if layout is not None:
        t["layout"] = layout
    if branding is not None:
        t["branding"] = branding
    if sections is not None:
        t["sections"] = sections
    t["published"] = False if t["version"] == 0 else t["published"]
    t["unpublished_changes"] = True
    return t

def set_role_view(role_id: str, view: Dict[str, Any]) -> Dict[str, Any]:
    t = _template() if TEMPLATE else None
    if t is None:
        create_template("Customer storefront", {"style": "grid", "hero": True}, {"colour": "#1A73E8"}, [])
        t = TEMPLATE
    _find(ROLES, "role_id", role_id)
    t["role_views"][role_id] = view
    return t

def publish_template(note: Optional[str]) -> Dict[str, Any]:
    t = _template()
    t.update({"version": t["version"] + 1, "published": True, "published_at": _now(), "version_note": note or "", "unpublished_changes": False})
    send_root_mail("template-published", None, f"The customer storefront was published as version {t['version']}.")
    return t
