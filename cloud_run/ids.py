"""
Identifiers - one place that makes them.
Every record (consumer, user, product, order, shipment, return, ticket, role, bid, passport, media file and the rest) is
identified by a UUID, written in lower-case with hyphens. Never build an id from text, and never read meaning out of one.

    new_id()           a fresh random id (uuid4) for a new record
    seed_id(name)      the same id every time for a name: used for the demo records, so they keep their id across restarts
    passport_id(pid)   the passport id of a product: one passport per product, with an id of its own
    is_uuid(value)     True for a well-formed UUID, so the API can answer 422 for a malformed id
"""

import uuid

_SEED = uuid.UUID("6f1c2a5e-8d3b-4c71-9a42-0b7e5d1f3c90")  # fixed: changing it changes every demo id
_PASSPORT = uuid.UUID("b3a9d4c2-71e5-4f08-a6c3-2d9e8f1b5a47")

def new_id() -> str:
    return str(uuid.uuid4())

def seed_id(name: str) -> str:
    return str(uuid.uuid5(_SEED, name))

def passport_id(product_id: str) -> str:
    return str(uuid.uuid5(_PASSPORT, str(product_id)))

def is_uuid(value) -> bool:
    try:
        return str(uuid.UUID(str(value))) == str(value).lower()
    except (ValueError, AttributeError, TypeError):
        return False
