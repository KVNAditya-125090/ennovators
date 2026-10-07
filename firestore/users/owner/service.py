"""
Firestore - Owner
The Owner is the product developer. Orders and shipments belong to the consumers and their customers,
so the Owner has no access to them here. The Owner does see the support tickets that consumers
raise with the platform team, and the queries visitors send from the home page.
"""

from typing import Dict, Any, List, Optional
from firestore.services.saas import firestore_saas

def list_platform_tickets() -> List[Dict[str, Any]]:
    return firestore_saas.list_platform_tickets()

def list_queries() -> List[Dict[str, Any]]:
    return firestore_saas.list_queries()

def update_query(query_id: str, status: str) -> Optional[Dict[str, Any]]:
    return firestore_saas.update_query(query_id, status)
