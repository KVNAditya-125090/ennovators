"""
Customer Router - utilizes the services via the consumer (storefront, support, AI assistant).
"""

import os
from fastapi import APIRouter, Body, HTTPException
from cloud_run.users.customer.schemas import QueryIn
from typing import Dict, Any
from firestore.users import customer as firestore
from vertex_ai.users import customer as vertex_ai
from cloud_storage.users import customer as cloud_storage
from cloud_sql.services.maas import cloud_sql_maas
from cloud_sql.services.maas.endpoints import endpoint_registry, SERVICE_ORDER
from cloud_run.access import customer_may_use, customer_brand, default_tenant_id
from firestore import store
from cloud_run.ids import passport_id

router = APIRouter(prefix="/api/v1/customer", tags=["Customer"])

# A customer registers with a consumer and shops only within that consumer's brand, so no consumer is assumed.
DEFAULT_CONSUMER = os.environ.get("DEFAULT_CONSUMER", "")

# The catalog fields the Customer portal needs to render and run a feature
_FIELDS = ("path", "service", "feature", "sub_category", "version", "actor", "category", "description", "method", "ai", "parameters")

@router.get("/endpoints")
def get_endpoints(tenant: str = DEFAULT_CONSUMER) -> Dict[str, Any]:
    """The Customer-side endpoints this consumer has switched on for its customers, grouped by service, with the
    consumer's id and brand so the portal can call through the gate and show the consumer's name (never the owner's)."""
    consumer = cloud_sql_maas.get_tenant_by_name(tenant) or cloud_sql_maas.get_tenant_by_name(DEFAULT_CONSUMER)
    if consumer is None:
        raise HTTPException(status_code=404, detail="Unknown consumer")
    services = {code: [] for code in SERVICE_ORDER}
    for e in endpoint_registry.list_endpoints():
        # opted in by the Owner, and shown by the consumer's published storefront template
        if e["actor"] == "Customer" and customer_may_use(consumer["tenant_id"], e["path"]):
            services[e["service"]].append({k: e[k] for k in _FIELDS})
    return {"tenant_id": consumer["tenant_id"], "consumer": consumer["name"], "services": services,
            "template": customer_brand(consumer["tenant_id"], consumer["name"])}

@router.get("/storefront")
def get_storefront() -> Dict[str, Any]:
    """The public storefront of the default consumer. A shopper's own tickets come through the signed-in endpoints, never here."""
    tenant = default_tenant_id()
    if tenant is None:
        return {"products": [], "tickets": []}
    store.set_tenant(tenant)
    return {"products": [{**p, "passport_id": passport_id(p["id"])} for p in firestore.browse_catalog() if not p.get("archived")], "tickets": []}

@router.post("/queries", status_code=201)
def send_query(query: QueryIn) -> Dict[str, Any]:
    """Anyone can ask a question from the home page. The team replies by email or phone."""
    saved = firestore.submit_query(query.name.strip(), query.email.strip(), query.mobile.strip(), query.message.strip())
    return {"query_id": saved["query_id"], "status": saved["status"]}

@router.post("/assistant")
def ask_assistant(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return vertex_ai.chat(data.get("message", ""), data.get("context", {}))

@router.post("/returns")
def start_return(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    item_id = data.get("item_id", "ITEM-DEFAULT")
    return {
        "upload": cloud_storage.create_upload_url(item_id, data.get("content_type", "image/jpeg")),
        "triage": vertex_ai.triage_return(item_id, data.get("image_url", ""))
    }
