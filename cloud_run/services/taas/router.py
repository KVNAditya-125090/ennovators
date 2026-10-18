"""
Transport as a Service (TaaS) Router
Handles moving goods A to B, shipment tracking, reverse logistics, and refurbisher dispatch.
"""

from fastapi import APIRouter, Header
from typing import Dict, Any, List, Optional
from urllib.parse import unquote
from firestore import store
from cloud_run.access import staff_tenant_id
from firestore.services.taas import firestore_taas
from cloud_run.ids import new_id

router = APIRouter(prefix="/api/v1/taas", tags=["Transport as a Service (TaaS)"])

@router.get("/shipments")
def get_shipments(x_user_email: Optional[str] = Header(None)) -> List[Dict[str, Any]]:
    store.set_tenant(staff_tenant_id(unquote(x_user_email) if x_user_email else None))
    return firestore_taas.list_shipments()

@router.post("/route/reverse")
def route_reverse_logistics(item_id: str, condition_grade: str) -> Dict[str, Any]:
    """Determines optimal transport route for returned items based on grade."""
    if "Grade A" in condition_grade:
        action = "Peer-to-Peer Direct Forwarding to Next Buyer"
        destination = "Next buyer"
    elif "Grade B" in condition_grade or "Grade C" in condition_grade:
        action = "Dispatch to Regional Refurbisher"
        destination = "Refurbisher"
    else:
        action = "Dispatch to E-Waste Recycling Hub"
        destination = "Recycler"

    return {
        "route_id": new_id(),
        "item_id": item_id,
        "input_grade": condition_grade,
        "optimized_action": action,
        "destination": destination,
        "distance_km": None,
        "estimated_freight_cost_usd": None,
        "carbon_efficiency_score": None
    }
