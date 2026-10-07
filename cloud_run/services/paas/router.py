"""
Product as a Service (PaaS) Router
Handles product catalog, Customer-to-Multi-Seller Bidding Protocol, surplus auctions, and forecasting.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from firestore.services.paas import firestore_paas
from bigquery.services.paas import bigquery_paas
from vertex_ai.services.paas import vertex_paas
import random

router = APIRouter(prefix="/api/v1/paas", tags=["Product as a Service (PaaS)"])

@router.get("/products")
def get_products() -> List[Dict[str, Any]]:
    return firestore_paas.list_products()

@router.get("/products/{product_id}")
def get_product(product_id: str) -> Dict[str, Any]:
    product = firestore_paas.get_product(product_id)
    return product if product else {"error": "Product not found"}

@router.post("/bids/open")
def open_bidding_room(product_id: str, max_budget: float) -> Dict[str, Any]:
    """Triggers the Customer-to-Multi-Seller Bidding Protocol."""
    matching_sellers = [
        {"seller_name": "Aura Official Store", "offer_price": round(max_budget * 0.95, 2), "condition": "New", "delivery_days": 2, "rating": 4.9},
        {"seller_name": "GreenCycle Refurbishers", "offer_price": round(max_budget * 0.78, 2), "condition": "Grade A Refurbished", "delivery_days": 3, "rating": 4.8},
        {"seller_name": "EcoHub Marketplace", "offer_price": round(max_budget * 0.85, 2), "condition": "Open-Box Excellent", "delivery_days": 1, "rating": 4.7}
    ]

    best_offer = min(matching_sellers, key=lambda x: x["offer_price"])

    return {
        "room_id": f"bid-room-{random.randint(1000, 9999)}",
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
        "model": "TimesFM Zero-Shot Forecast (Quantized CPU)",
        "recommended_reorder_point": 18,
        "forecast_period": "14 Days",
        "daily_forecast": forecast_data
    }
