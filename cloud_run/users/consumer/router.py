"""
Consumer Router - consumes the services (MaaS workspace, PaaS catalog, TaaS shipments, demand forecast).
One call returns everything the Consumer console needs. A feature whose endpoint the Owner has not opted this workspace into for this
workspace returns no data and is listed in disabled_apis.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from cloud_sql.users import consumer as cloud_sql
from firestore.users import consumer as firestore
from bigquery.users import consumer as bigquery
from vertex_ai.users import consumer as vertex_ai
from cloud_run.access import allowed_paths, role_view

router = APIRouter(prefix="/api/v1/consumer", tags=["Consumer"])

FEATURES = {"workspace-management", "product-catalog", "shipment-tracking", "demand-forecast"}

@router.get("/dashboard")
def get_dashboard(sku: str = "SKU-WATCH-G3", tenant: str = "GreenCycle Refurbishers") -> Dict[str, Any]:
    enabled = cloud_sql.enabled_features(tenant)
    if enabled is None:  # unknown workspace: nothing is switched off
        enabled = set(FEATURES)
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
        "disabled_apis": sorted(FEATURES - enabled)
    }

@router.get("/endpoints")
def get_endpoints(tenant: str = "GreenCycle Refurbishers", email: str = "") -> Dict[str, Any]:
    """The endpoints this workspace has opted into that this person may use, grouped by service, and the pages their role shows."""
    services = cloud_sql.list_opted_endpoints(tenant)
    if services is None:
        raise HTTPException(status_code=404, detail="Unknown workspace")
    allowed = allowed_paths(email, tenant)
    if allowed is not None:
        services = {code: [e for e in items if e["path"] in allowed] for code, items in services.items()}
    # the pages the Root chose for this person's role on the Customization page (None: no narrowing)
    return {"services": services, "view": role_view(email, tenant)}
