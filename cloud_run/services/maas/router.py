"""
Management as a Service (MaaS) Router
Handles role access, tenant configuration, system health, and budget tracking.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from cloud_sql.services.maas import cloud_sql_maas
from bigquery.services.maas import bigquery_maas
from cloud_run.services.maas.schemas import LoginRequest

router = APIRouter(prefix="/api/v1/maas", tags=["Management as a Service (MaaS)"])

@router.get("/health")
def get_system_health() -> Dict[str, Any]:
    return {
        "status": "Healthy",
        "service": "AuraCommerce 360 Core API",
        "mode": "Preview",
        "components": {
            "API": "Active (auto-scaling)",
            "Sign-in": "Connected",
            "AI": "Active",
            "Database": "Active (sample data)"
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

@router.post("/auth/login")
def login(credentials: LoginRequest) -> Dict[str, Any]:
    """Single sign-in: the account decides the role, and the role decides the portal."""
    user = cloud_sql_maas.authenticate(credentials.email, credentials.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"user": user}
