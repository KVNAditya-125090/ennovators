"""
Management as a Service (MaaS) Router
Handles role access, tenant configuration, system health, and budget tracking.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from cloud_sql.services.maas import cloud_sql_maas
from bigquery.services.maas import bigquery_maas

router = APIRouter(prefix="/api/v1/maas", tags=["Management as a Service (MaaS)"])

@router.get("/health")
def get_system_health() -> Dict[str, Any]:
    return {
        "status": "Healthy",
        "service": "AuraCommerce 360 Core API (Cloud Run)",
        "gcp_mode": "Keyless Preview Mode",
        "components": {
            "Cloud Run": "Active (Scale to zero)",
            "Firebase Auth": "Connected (Mock/Configured)",
            "Vertex AI Adapter": "Mock Active (Gemini Flash)",
            "Database": "Cloud SQL / PostgreSQL (Simulated)"
        }
    }

@router.get("/tenants")
def get_tenants() -> List[Dict[str, Any]]:
    return cloud_sql_maas.list_tenants()

@router.get("/users")
def get_users() -> List[Dict[str, Any]]:
    return cloud_sql_maas.list_users()

@router.get("/budget-status")
def get_budget_status() -> Dict[str, Any]:
    return bigquery_maas.get_budget_status()
