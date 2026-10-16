"""
Firestore - Customer
What the Customer (shopper, via the consumer) reads: the storefront catalog and support tickets.
"""

from typing import Dict, Any, List
from firestore.services.paas import firestore_paas
from firestore.services.saas import firestore_saas

def browse_catalog() -> List[Dict[str, Any]]:
    return firestore_paas.list_products()

def my_tickets() -> List[Dict[str, Any]]:
    return firestore_saas.list_tickets()

def submit_query(name: str, email: str, mobile: str, message: str) -> Dict[str, Any]:
    """A query sent from the home page by anyone, signed in or not."""
    return firestore_saas.add_query(name, email, mobile, message)
