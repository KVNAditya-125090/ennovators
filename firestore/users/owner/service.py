"""
Firestore - Owner
The Owner operates all four services, so it oversees every collection:
PaaS products, TaaS shipments and SaaS tickets.
"""

from typing import Dict, Any, List
from firestore.services.paas import firestore_paas
from firestore.services.taas import firestore_taas
from firestore.services.saas import firestore_saas

def list_products() -> List[Dict[str, Any]]:
    return firestore_paas.list_products()

def list_shipments() -> List[Dict[str, Any]]:
    return firestore_taas.list_shipments()

def list_tickets() -> List[Dict[str, Any]]:
    return firestore_saas.list_tickets()
