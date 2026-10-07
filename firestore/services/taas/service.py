"""
Firestore - TaaS (Transport as a Service)
Document collection: shipments.
"""

from typing import Dict, Any, List

SHIPMENTS = [
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

class FirestoreTaaS:
    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def list_shipments(self) -> List[Dict[str, Any]]:
        return SHIPMENTS

firestore_taas = FirestoreTaaS()
