"""
Firestore - TaaS (Transport as a Service)
Document collection: shipments.
"""

from typing import Dict, Any, List

from firestore import store

class FirestoreTaaS:
    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def list_shipments(self) -> List[Dict[str, Any]]:
        return store.rows("shipments", "shipment_id")

firestore_taas = FirestoreTaaS()
