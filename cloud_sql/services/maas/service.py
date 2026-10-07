"""
Cloud SQL (PostgreSQL) - MaaS (Management as a Service)
Relational, multi-tenant system of record: tenants, users and RBAC roles.
"""

from typing import Dict, Any, List

TENANTS = [
    {"tenant_id": "t-001", "name": "Aura Eco Retail", "type": "Primary Retailer", "status": "Active", "users_count": 42},
    {"tenant_id": "t-002", "name": "GreenCycle Refurbishers", "type": "Certified Refurbisher", "status": "Active", "users_count": 18},
    {"tenant_id": "t-003", "name": "NextLife Electronics", "type": "Third-Party Seller", "status": "Active", "users_count": 9}
]

USERS = [
    {"user_id": "usr-101", "name": "Aditya Kothapalli", "email": "admin@auracommerce.io", "role": "Owner / SuperAdmin", "tenant": "Aura Eco Retail"},
    {"user_id": "usr-102", "name": "Sarah Chen", "email": "seller@greencycle.com", "role": "Consumer / Seller", "tenant": "GreenCycle Refurbishers"},
    {"user_id": "usr-103", "name": "Marcus Vance", "email": "customer@gmail.com", "role": "Customer", "tenant": "Direct Shopper"}
]

class CloudSQLMaaS:
    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def list_tenants(self) -> List[Dict[str, Any]]:
        return TENANTS

    def list_users(self) -> List[Dict[str, Any]]:
        return USERS

cloud_sql_maas = CloudSQLMaaS()
