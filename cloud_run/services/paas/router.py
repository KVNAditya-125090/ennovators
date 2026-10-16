"""
Product as a Service (PaaS) Router
Handles product catalog, Customer-to-Multi-Seller Bidding Protocol, surplus auctions, and forecasting.
"""

from fastapi import APIRouter, Body, Header, HTTPException
from typing import Optional
from cloud_sql.services.maas import cloud_sql_maas
from cloud_run.access import customer_may_use
from typing import Dict, Any, List
from firestore.services.paas import firestore_paas
from bigquery.services.paas import bigquery_paas
from vertex_ai.services.paas import vertex_paas
import random
from cloud_run.ids import new_id

router = APIRouter(prefix="/api/v1/paas", tags=["Product as a Service (PaaS)"])

DEFAULT_CONSUMER = "GreenCycle Refurbishers"  # the consumer whose storefront the demo shopper uses

def _require_customer_feature(path: str, tenant_id: Optional[str]) -> None:
    """These older shopper routes answer only while the Owner has opted the consumer into the matching catalog
    endpoint and the consumer's published storefront still shows it (the same rule the gate applies)."""
    tenant = cloud_sql_maas.get_tenant(tenant_id) if tenant_id else cloud_sql_maas.get_tenant_by_name(DEFAULT_CONSUMER)
    if tenant is None or not customer_may_use(tenant["tenant_id"], path):
        raise HTTPException(status_code=403, detail={"code": "not_purchased", "message": "This seller does not offer this feature."})

@router.post("/assistant/chat/text-to-text")
def chat_with_assistant(data: Dict[str, Any] = Body(...), x_tenant_id: Optional[str] = Header(None)) -> Dict[str, Any]:
    _require_customer_feature("/paas/assistant/chat/text-to-text/v1", x_tenant_id)
    return vertex_paas.chat_assistant(data.get("message", ""), data.get("context", {}))

@router.get("/products")
def get_products() -> List[Dict[str, Any]]:
    return firestore_paas.list_products()

@router.get("/products/{product_id}")
def get_product(product_id: str) -> Dict[str, Any]:
    product = firestore_paas.get_product(product_id)
    return product if product else {"error": "Product not found"}

@router.post("/bids/open")
def open_bidding_room(product_id: str, max_budget: float, x_tenant_id: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Triggers the Customer-to-Multi-Seller Bidding Protocol."""
    _require_customer_feature("/paas/bid/multi-seller/open/v1", x_tenant_id)
    matching_sellers = [
        {"seller_name": "Aura Official Store", "offer_price": round(max_budget * 0.95, 2), "condition": "New", "delivery_days": 2, "rating": 4.9},
        {"seller_name": "GreenCycle Refurbishers", "offer_price": round(max_budget * 0.78, 2), "condition": "Grade A Refurbished", "delivery_days": 3, "rating": 4.8},
        {"seller_name": "EcoHub Marketplace", "offer_price": round(max_budget * 0.85, 2), "condition": "Open-Box Excellent", "delivery_days": 1, "rating": 4.7}
    ]

    best_offer = min(matching_sellers, key=lambda x: x["offer_price"])

    return {
        "room_id": new_id(),
        "product_id": product_id,
        "customer_max_budget": max_budget,
        "status": "AUCTION_ACTIVE",
        "participating_sellers": len(matching_sellers),
        "offers": matching_sellers,
        "winning_best_fit": best_offer,
        "carbon_saving_vs_new": "3.8 kg CO2e"
    }

@router.get("/forecast/demand/{sku}")
def get_demand_forecast(sku: str) -> Dict[str, Any]:
    history = bigquery_paas.get_demand_history(sku)
    forecast_data = vertex_paas.predict_demand_timesfm(sku, history)
    return {
        "sku": sku,
        "model": "AI demand forecast",
        "recommended_reorder_point": 18,
        "forecast_period": "14 Days",
        "daily_forecast": forecast_data
    }
