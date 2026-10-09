"""
Cloud SQL - Owner
What the Owner reads and changes: the consumers (tenants), their teams and which endpoints each has opted into.
"""

from typing import Dict, Any, List, Optional
from cloud_sql.services.maas import cloud_sql_maas
from cloud_sql.services.maas.endpoints import endpoint_registry, MAX_RATE_LIMIT, MAX_MONTHLY_FEE, MAX_PRICE_PER_1K, SETTING_KEYS, default_settings

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

def list_endpoints(service: Optional[str] = None) -> List[Dict[str, Any]]:
    return endpoint_registry.list_endpoints(service)

def enabled_endpoint_paths(tenant_id: str) -> set:
    return endpoint_registry.enabled_paths(tenant_id)

def endpoint_service_summary(tenant_id: str) -> Dict[str, Dict[str, Any]]:
    return endpoint_registry.service_summary(tenant_id)

def set_endpoint_enabled(tenant_id: str, path: str, enabled: bool) -> str:
    return endpoint_registry.set_endpoint_enabled(tenant_id, path, enabled)

def set_service_enabled(tenant_id: str, service: str, enabled: bool) -> str:
    return endpoint_registry.set_service_enabled(tenant_id, service, enabled)

def endpoint_settings(tenant_id: str) -> Dict[str, Dict[str, Any]]:
    return endpoint_registry.endpoint_settings(tenant_id)

def update_endpoint_settings(tenant_id: str, path: str, values: Dict[str, Any], reset: bool = False) -> str:
    return endpoint_registry.update_settings(tenant_id, path, values, reset)

def endpoint_defaults(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    return default_settings(endpoint)

def list_audit(tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    return endpoint_registry.list_audit(tenant_id, limit)
