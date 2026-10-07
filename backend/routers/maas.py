"""
Management as a Service (MaaS) Router
Handles role access, tenant configuration, system health, and budget tracking.
"""

from fastapi import APIRouter
from typing import Dict, Any, List

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
    return [
        {"tenant_id": "t-001", "name": "Aura Eco Retail", "type": "Primary Retailer", "status": "Active", "users_count": 42},
        {"tenant_id": "t-002", "name": "GreenCycle Refurbishers", "type": "Certified Refurbisher", "status": "Active", "users_count": 18},
        {"tenant_id": "t-003", "name": "NextLife Electronics", "type": "Third-Party Seller", "status": "Active", "users_count": 9}
    ]

@router.get("/users")
def get_users() -> List[Dict[str, Any]]:
    return [
        {"user_id": "usr-101", "name": "Aditya Kothapalli", "email": "admin@auracommerce.io", "role": "Owner / SuperAdmin", "tenant": "Aura Eco Retail"},
        {"user_id": "usr-102", "name": "Sarah Chen", "email": "seller@greencycle.com", "role": "Consumer / Seller", "tenant": "GreenCycle Refurbishers"},
        {"user_id": "usr-103", "name": "Marcus Vance", "email": "customer@gmail.com", "role": "Customer", "tenant": "Direct Shopper"}
    ]

@router.get("/budget-status")
def get_budget_status() -> Dict[str, Any]:
    return {
        "budget_limit_usd": 120.00,
        "spent_to_date_usd": 18.45,
        "remaining_usd": 101.55,
        "percentage_used": 15.37,
        "alerts": [
            {"threshold": "50%", "status": "OK"},
            {"threshold": "75%", "status": "OK"},
            {"threshold": "90%", "status": "OK"},
            {"threshold": "100% (Kill Switch)", "status": "ARMED"}
        ]
    }

