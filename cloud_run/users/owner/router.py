"""
Owner Router - operates all four services (MaaS, PaaS, TaaS, SaaS).
One call returns everything the Owner console needs.
"""

from fastapi import APIRouter
from typing import Dict, Any
from cloud_run.services.maas import get_system_health
from cloud_sql.users import owner as cloud_sql
from bigquery.users import owner as bigquery
from firestore.users import owner as firestore

router = APIRouter(prefix="/api/v1/owner", tags=["Owner"])

@router.get("/overview")
def get_overview() -> Dict[str, Any]:
    tenants = cloud_sql.list_tenants()
    users = cloud_sql.list_users()
    products = firestore.list_products()
    shipments = firestore.list_shipments()
    tickets = firestore.list_tickets()
    return {
        "health": get_system_health(),
        "budget": bigquery.get_budget_status(),
        "tenants": tenants,
        "users": users,
        "services": {
            "maas": {"name": "Management as a Service", "tenants": len(tenants), "users": len(users)},
            "paas": {"name": "Product as a Service", "products": len(products)},
            "taas": {"name": "Transport as a Service", "shipments": len(shipments),
                     "in_transit": sum(1 for s in shipments if s["status"] == "In Transit")},
            "saas": {"name": "Support as a Service", "tickets": len(tickets),
                     "open_tickets": sum(1 for t in tickets if t["status"] != "Resolved")}
        }
    }
