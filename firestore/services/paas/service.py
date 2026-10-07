"""
Firestore - PaaS (Product as a Service)
Document collection: product catalog.
"""

from typing import Dict, Any, List, Optional

PRODUCTS = [
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

class FirestorePaaS:
    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def list_products(self) -> List[Dict[str, Any]]:
        return PRODUCTS

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        return next((p for p in PRODUCTS if p["id"] == product_id), None)

firestore_paas = FirestorePaaS()
