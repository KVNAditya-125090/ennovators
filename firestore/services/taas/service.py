"""
Firestore - TaaS (Transport as a Service)
Document collection: shipments.
"""

from typing import Dict, Any, List

SHIPMENTS = [
    {
        "shipment_id": "d5a367a9-dd4e-5ffc-906a-ea671c03e994",
        "type": "Forward Delivery",
        "origin": "Central Warehouse (Bengaluru)",
        "destination": "Customer (Hyderabad)",
        "status": "in_transit",
        "carrier": "EcoExpress Zero-Emission Electric",
        "eta": "Tomorrow, 4:00 PM",
        "co2_saved_kg": 1.8
    },
    {
        "shipment_id": "dae6a021-b92f-5249-b030-7d214755d3f4",
        "type": "Reverse Logistics (Direct Peer Forward)",
        "origin": "Returning Customer (Mumbai)",
        "destination": "New Buyer (Pune)",
        "status": "created",
        "carrier": "Peer2Peer Green Relay",
        "eta": "Oct 9, 2026",
        "co2_saved_kg": 4.5
    },
    {
        "shipment_id": "22cabb1b-5492-5aa5-9a7b-b8a9397e9393",
        "type": "Refurbishment Dispatch",
        "origin": "Collection Hub (Chennai)",
        "destination": "GreenCycle Certified Lab (Bengaluru)",
        "status": "delivered",
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
