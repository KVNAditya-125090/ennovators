"""
Consumer Router - consumes the services (MaaS workspace, PaaS catalog, TaaS shipments, demand forecast).
One call returns everything the Consumer console needs. An API the Owner has switched off for this
workspace returns no data and is listed in disabled_apis.
"""

from fastapi import APIRouter
from typing import Dict, Any
from cloud_sql.users import consumer as cloud_sql
from firestore.users import consumer as firestore
from bigquery.users import consumer as bigquery
from vertex_ai.users import consumer as vertex_ai

router = APIRouter(prefix="/api/v1/consumer", tags=["Consumer"])

ALL_APIS = {"workspace-management", "product-catalog", "shipment-tracking", "demand-forecast"}

@router.get("/dashboard")
def get_dashboard(sku: str = "SKU-WATCH-G3", tenant: str = "GreenCycle Refurbishers") -> Dict[str, Any]:
    enabled = cloud_sql.enabled_api_ids(tenant)
    if enabled is None:  # unknown workspace: nothing is switched off
        enabled = set(ALL_APIS)
    workspace = cloud_sql.get_workspace(tenant) if "workspace-management" in enabled else None

    forecast = None
    if "demand-forecast" in enabled:
        history = bigquery.get_demand_history(sku)
        forecast = {
            "sku": sku,
            "model": "AI demand forecast",
            "recommended_reorder_point": 18,
            "forecast_period": "14 Days",
            "daily_forecast": vertex_ai.forecast_demand(sku, history)
        }

    return {
        "workspace": None if workspace is None else {**workspace, "usage": bigquery.get_workspace_usage(tenant)},
        "products": firestore.browse_catalog() if "product-catalog" in enabled else None,
        "shipments": firestore.track_shipments() if "shipment-tracking" in enabled else None,
        "forecast": forecast,
        "disabled_apis": sorted(ALL_APIS - enabled)
    }
