"""
Product as a Service (PaaS) Router
Handles product catalog, Customer-to-Multi-Seller Bidding Protocol, surplus auctions, and forecasting.
"""

import os
from fastapi import APIRouter, Body, Header, HTTPException
from typing import Optional
from cloud_sql.services.maas import cloud_sql_maas
from cloud_run.access import customer_may_use, default_tenant_id
from urllib.parse import unquote
from cloud_run import assistant_facts, customer_handlers, forecast_math
from firestore.users.consumer import operations as ops
from firestore import store
from typing import Dict, Any, List
from firestore.services.paas import firestore_paas
from bigquery.services.paas import bigquery_paas
from vertex_ai.services.paas import vertex_paas
from cloud_run.ids import new_id

router = APIRouter(prefix="/api/v1/paas", tags=["Product as a Service (PaaS)"])

DEFAULT_CONSUMER = os.environ.get("DEFAULT_CONSUMER", "")  # no consumer is assumed: a shopper names the consumer they shop with

def _require_customer_feature(path: str, tenant_id: Optional[str]) -> Dict[str, Any]:
    """These older shopper routes answer only while the Owner has opted the consumer into the matching catalog
    endpoint and the consumer's published storefront still shows it (the same rule the gate applies)."""
    tenant = cloud_sql_maas.get_tenant(tenant_id) if tenant_id else cloud_sql_maas.get_tenant_by_name(DEFAULT_CONSUMER)
    if tenant is None or not customer_may_use(tenant["tenant_id"], path):
        raise HTTPException(status_code=403, detail={"code": "not_purchased", "message": "This seller does not offer this feature."})
    return tenant

@router.post("/assistant/chat/text-to-text")
def chat_with_assistant(data: Dict[str, Any] = Body(...), x_tenant_id: Optional[str] = Header(None)) -> Dict[str, Any]:
    tenant = _require_customer_feature("/paas/assistant/chat/text-to-text/v1", x_tenant_id)
    store.set_tenant(tenant["tenant_id"])
    context = {**(data.get("context") or {}), "topic": "shopping", "facts": assistant_facts.build(tenant, "shopping")}
    return vertex_paas.chat_assistant(data.get("message", ""), context)

@router.get("/products")
def get_products() -> List[Dict[str, Any]]:
    """The public catalog of the default consumer: products that are still on sale."""
    tenant = default_tenant_id()
    if tenant is None:
        return []
    store.set_tenant(tenant)
    return [p for p in firestore_paas.list_products() if not p.get("archived")]

@router.get("/products/{product_id}")
def get_product(product_id: str) -> Dict[str, Any]:
    tenant = default_tenant_id()
    if tenant is None:
        return {"error": "Product not found"}
    store.set_tenant(tenant)
    product = firestore_paas.get_product(product_id)
    return product if product and not product.get("archived") else {"error": "Product not found"}

@router.post("/bids/open")
def open_bidding_room(product_id: str, max_budget: float, x_tenant_id: Optional[str] = Header(None), x_user_email: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Triggers the Customer-to-Multi-Seller Bidding Protocol."""
    tenant = _require_customer_feature("/paas/bid/multi-seller/open/v1", x_tenant_id)
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Sign in to open a bidding room.")
    ops.CUSTOMER.set(unquote(x_user_email).strip().lower())
    store.set_tenant(tenant["tenant_id"])
    product = next((p for p in firestore_paas.list_products() if p["id"] == product_id or p.get("sku") == product_id), None)
    if product is None:
        raise HTTPException(status_code=404, detail="No such product.")
    try:
        return customer_handlers.open_room(tenant, product, max_budget)
    except ValueError as problem:
        raise HTTPException(status_code=422, detail=str(problem))

@router.get("/forecast/demand/{sku}")
def get_demand_forecast(sku: str) -> Dict[str, Any]:
    history = bigquery_paas.get_demand_history(sku)
    forecast_data = vertex_paas.predict_demand_timesfm(sku, history)
    return {
        "sku": sku,
        "model": "AI demand forecast",
        "recommended_reorder_point": forecast_math.reorder_point(history, forecast_data),
        "forecast_period": "14 Days",
        "daily_forecast": forecast_data
    }
