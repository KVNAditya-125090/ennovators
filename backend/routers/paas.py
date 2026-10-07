"""
Product as a Service (PaaS) Router
Handles product catalog, Customer-to-Multi-Seller Bidding Protocol, surplus auctions, and forecasting.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from services.vertex_mock import vertex_service
import random

router = APIRouter(prefix="/api/v1/paas", tags=["Product as a Service (PaaS)"])

MOCK_PRODUCTS = [
    {
        "id": "prod-001",
        "name": "Aura Smart Eco Watch (Gen 3)",
        "sku": "SKU-WATCH-G3",
        "category": "Electronics",
        "retail_price": 249.99,
        "current_bidding_floor": 180.00,
        "condition": "New / Factory Sealed",
        "stock": 14,
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop",
        "carbon_footprint_kg": 4.2
    },
    {
        "id": "prod-002",
        "name": "Circular Noise-Canceling Headphones",
        "sku": "SKU-AUDIO-NC2",
        "category": "Audio",
        "retail_price": 199.00,
        "current_bidding_floor": 135.00,
        "condition": "Certified Refurbished (Grade A)",
        "stock": 8,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop",
        "carbon_footprint_kg": 2.1
    },
    {
        "id": "prod-003",
        "name": "Modular Solar Power Bank 20,000mAh",
        "sku": "SKU-POWER-SOLAR",
        "category": "Accessories",
        "retail_price": 89.50,
        "current_bidding_floor": 62.00,
        "condition": "New / Factory Sealed",
        "stock": 25,
        "image_url": "https://images.unsplash.com/photo-1609592424109-dd9892f1b177?w=500&auto=format&fit=crop",
        "carbon_footprint_kg": 1.5
    }
]

@router.get("/products")
def get_products() -> List[Dict[str, Any]]:
    return MOCK_PRODUCTS

@router.get("/products/{product_id}")
def get_product(product_id: str) -> Dict[str, Any]:
    for p in MOCK_PRODUCTS:
        if p["id"] == product_id:
            return p
    return {"error": "Product not found"}

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
    forecast_data = vertex_service.predict_demand_timesfm(sku)
    return {
        "sku": sku,
        "model": "TimesFM Zero-Shot Forecast (Quantized CPU)",
        "recommended_reorder_point": 18,
        "forecast_period": "14 Days",
        "daily_forecast": forecast_data
    }

