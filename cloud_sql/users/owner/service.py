"""
Cloud SQL - Owner
What the Owner reads and changes: the consumers (tenants), their teams and which APIs are enabled for each.
"""

from typing import Dict, Any, List, Optional
from cloud_sql.services.maas import cloud_sql_maas

def list_tenants() -> List[Dict[str, Any]]:
    return cloud_sql_maas.list_tenants()

def list_users() -> List[Dict[str, Any]]:
    return cloud_sql_maas.list_users()

def get_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
    return cloud_sql_maas.get_tenant(tenant_id)

def list_members(tenant_name: str) -> List[Dict[str, Any]]:
    return cloud_sql_maas.list_members(tenant_name)

def get_profile(tenant_id: str) -> Optional[Dict[str, Any]]:
    return cloud_sql_maas.get_profile(tenant_id)

def get_api_catalog() -> List[Dict[str, Any]]:
    return cloud_sql_maas.list_api_catalog()

def get_limit_fields(api_id: str) -> List[Dict[str, Any]]:
    return cloud_sql_maas.get_limit_fields(api_id)

def get_api_settings(tenant_id: str) -> Dict[str, Dict[str, Any]]:
    return cloud_sql_maas.get_api_settings(tenant_id)

def update_api_settings(tenant_id: str, api_id: str, values: Dict[str, Any]) -> bool:
    return cloud_sql_maas.update_api_settings(tenant_id, api_id, values)

def reset_api_settings(tenant_id: str, api_id: str) -> bool:
    return cloud_sql_maas.reset_api_settings(tenant_id, api_id)

def enabled_api_ids(tenant_id: str) -> set:
    return cloud_sql_maas.enabled_api_ids(tenant_id)

def set_api_enabled(tenant_id: str, api_id: str, enabled: bool) -> bool:
    return cloud_sql_maas.set_api_enabled(tenant_id, api_id, enabled)
