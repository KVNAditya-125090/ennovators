"""
Firestore - Consumer
What the Consumer (service operator/seller) reads: the catalog it lists and the shipments it moves.
"""

from typing import Dict, Any, List
from firestore.services.paas import firestore_paas
from firestore.services.taas import firestore_taas

def browse_catalog() -> List[Dict[str, Any]]:
    return firestore_paas.list_products()

def track_shipments() -> List[Dict[str, Any]]:
    return firestore_taas.list_shipments()
