"""
Consumer Router - consumes the services (PaaS catalog, TaaS shipments, demand forecast).
One call returns everything the Consumer console needs.
"""

from fastapi import APIRouter
from typing import Dict, Any
from firestore.users import consumer as firestore
from bigquery.users import consumer as bigquery
from vertex_ai.users import consumer as vertex_ai

router = APIRouter(prefix="/api/v1/consumer", tags=["Consumer"])

@router.get("/dashboard")
def get_dashboard(sku: str = "SKU-WATCH-G3") -> Dict[str, Any]:
    history = bigquery.get_demand_history(sku)
    return {
        "products": firestore.browse_catalog(),
        "shipments": firestore.track_shipments(),
        "forecast": {
            "sku": sku,
            "model": "TimesFM Zero-Shot Forecast (Quantized CPU)",
            "recommended_reorder_point": 18,
            "forecast_period": "14 Days",
            "daily_forecast": vertex_ai.forecast_demand(sku, history)
        }
    }
