"""
Cloud SQL - Owner
What the Owner reads: tenant and user listings for role access management.
"""

from typing import Dict, Any, List
from cloud_sql.services.maas import cloud_sql_maas

def list_tenants() -> List[Dict[str, Any]]:
    return cloud_sql_maas.list_tenants()

def list_users() -> List[Dict[str, Any]]:
    return cloud_sql_maas.list_users()
