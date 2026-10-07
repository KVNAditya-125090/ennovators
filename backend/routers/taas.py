"""
Transport as a Service (TaaS) Router
Handles moving goods A to B, shipment tracking, reverse logistics, and refurbisher dispatch.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
import random

router = APIRouter(prefix="/api/v1/taas", tags=["Transport as a Service (TaaS)"])

MOCK_SHIPMENTS = [
    {
        "shipment_id": "shp-901",
        "type": "Forward Delivery",
        "origin": "Central Warehouse (Bengaluru)",
        "destination": "Customer (Hyderabad)",
        "status": "In Transit",
        "carrier": "EcoExpress Zero-Emission Electric",
        "eta": "Tomorrow, 4:00 PM",
        "co2_saved_kg": 1.8
    },
    {
        "shipment_id": "shp-902",
        "type": "Reverse Logistics (Direct Peer Forward)",
        "origin": "Returning Customer (Mumbai)",
        "destination": "New Buyer (Pune)",
        "status": "Pickup Scheduled",
        "carrier": "Peer2Peer Green Relay",
        "eta": "Oct 9, 2026",
        "co2_saved_kg": 4.5
    },
    {
        "shipment_id": "shp-903",
        "type": "Refurbishment Dispatch",
        "origin": "Collection Hub (Chennai)",
        "destination": "GreenCycle Certified Lab (Bengaluru)",
        "status": "Delivered",
        "carrier": "Partner Logistics",
        "eta": "Delivered Oct 6",
        "co2_saved_kg": 3.2
    }
]

@router.get("/shipments")
def get_shipments() -> List[Dict[str, Any]]:
    return MOCK_SHIPMENTS

@router.post("/route/reverse")
def route_reverse_logistics(item_id: str, condition_grade: str) -> Dict[str, Any]:
    """Determines optimal transport route for returned items based on grade."""
    if "Grade A" in condition_grade:
        action = "Peer-to-Peer Direct Forwarding to Next Buyer"
        destination = "Next Customer Order #ORD-8821"
    elif "Grade B" in condition_grade or "Grade C" in condition_grade:
        action = "Dispatch to Regional Refurbisher"
        destination = "GreenCycle Certified Repair Lab"
    else:
        action = "Dispatch to E-Waste Recycling Hub"
        destination = "Certified Cradle-to-Cradle Recycler"
        
    return {
        "route_id": f"rev-route-{random.randint(100,999)}",
        "item_id": item_id,
        "input_grade": condition_grade,
        "optimized_action": action,
        "destination": destination,
        "distance_km": round(random.uniform(12.0, 180.0), 1),
        "estimated_freight_cost_usd": round(random.uniform(3.50, 12.00), 2),
        "carbon_efficiency_score": "A+"
    }

