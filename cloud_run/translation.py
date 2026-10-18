"""
Cloud Run - listing and ticket translation
Translates a product listing, or a support ticket and its replies, into one of the app's nine languages with Gemini.

A listing translation is kept on the product (product["translations"][language]) together with a hash of the text it was made
from, so asking again for an unchanged listing costs nothing and an edited listing is translated afresh. A ticket translation
is returned, not kept (tickets keep changing). If Gemini cannot be reached the call is refused with a plain message: a wrong
or invented translation is worse than none.
"""

import datetime
import hashlib
from typing import Any, Callable, Dict

from firestore.users.consumer import operations as ops
from vertex_ai import gemini

LANGUAGES = gemini.LANGUAGE_NAMES  # code -> English name


def _code(value: Any) -> str:
    """The language code for a code ("hi") or an English name ("Hindi"); anything else is refused."""
    text = str(value or "").strip().lower()
    for code, name in LANGUAGES.items():
        if text in (code, name.lower()):
            return code
    raise ValueError("Pick one of: " + ", ".join(f"{n} ({c})" for c, n in LANGUAGES.items()) + ".")


def _stamp(fields: Dict[str, str]) -> str:
    return hashlib.sha1("\x1f".join(f"{k}={v}" for k, v in sorted(fields.items())).encode("utf-8")).hexdigest()[:12]


def _translate(fields: Dict[str, str], code: str) -> Dict[str, str]:
    result = gemini.translate(fields, code)
    if result is None:
        raise ValueError("Translation is not available right now. Please try again in a moment.")
    return result


def translate_listing(tenant, params):
    code = _code(params["target_language"])
    product = next((p for p in ops.list_products() if p["id"] == params["product_id"] or p.get("sku") == params["product_id"]), None)
    if product is None:
        raise LookupError(f"No product {params['product_id']}")
    source = {"name": str(product.get("name") or "")}
    if product.get("description"):
        source["description"] = str(product["description"])
    stamp = _stamp(source)
    saved = (product.get("translations") or {}).get(code)
    if code == "en" or (saved and saved.get("source_hash") == stamp):
        return {"product_id": product["id"], "language": code, "cached": code != "en", **(saved or {"name": source["name"], "description": source.get("description", "")}),
                "source": {"name": source["name"], "description": source.get("description", "")}}
    done = _translate(source, code)
    entry = {"name": done["name"], "description": done.get("description", ""), "source_hash": stamp, "translated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"), "by": "Gemini"}
    product.setdefault("translations", {})[code] = entry
    return {"product_id": product["id"], "language": code, "cached": False, **entry, "source": {"name": source["name"], "description": source.get("description", "")}}


def translate_ticket(tenant, params):
    code = _code(params["target_language"])
    ticket = next((t for t in ops.read_tickets(None) if t["ticket_id"] == params["ticket_id"]), None)
    if ticket is None:
        raise LookupError(f"No ticket {params['ticket_id']}")
    fields = {"subject": str(ticket.get("subject") or "")}
    for i, m in enumerate(ticket.get("messages") or []):
        fields[f"m{i}"] = str(m.get("text") or m.get("message") or "")
    fields = {k: v for k, v in fields.items() if v.strip()}
    done = _translate(fields, code)
    messages = [{"from": m.get("from"), "text": done.get(f"m{i}", "")} for i, m in enumerate(ticket.get("messages") or []) if f"m{i}" in done]
    return {"ticket_id": ticket["ticket_id"], "language": code, "subject": done.get("subject", ""), "messages": messages, "by": "Gemini"}


def install(handlers: Dict[str, Callable]) -> int:
    table = {"/paas/locale/listing/translate/v1": translate_listing, "/saas/locale/ticket/translate/v1": translate_ticket}
    handlers.update(table)
    return len(table)
