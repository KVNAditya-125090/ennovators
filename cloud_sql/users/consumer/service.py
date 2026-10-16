"""
Cloud SQL - Consumer
What the Consumer reads: its own tenant workspace and team, through Management as a Service.
"""

from typing import Dict, Any, Optional, Set
from cloud_sql.services.maas import cloud_sql_maas
from cloud_sql.services.maas.endpoints import endpoint_registry, SERVICE_ORDER

def get_workspace(tenant_name: str) -> Optional[Dict[str, Any]]:
    return cloud_sql_maas.get_workspace(tenant_name)

# The consumer console's features and the catalog endpoint each one is opted into through
FEATURE_ENDPOINTS = {
    "workspace-management": "/maas/user/staff/list/v1",
    "product-catalog": "/paas/catalog/product/read/v1",
    "shipment-tracking": "/taas/shipment/read/staff/v1",
    "demand-forecast": "/paas/forecast/demand/read/v1",
}

def enabled_features(tenant_name: str) -> Optional[Set[str]]:
    """The console features this workspace has opted into, or None if the workspace is unknown."""
    tenant = cloud_sql_maas.get_tenant_by_name(tenant_name)
    if tenant is None:
        return None
    opted = endpoint_registry.enabled_paths(tenant["tenant_id"])
    return {feature for feature, path in FEATURE_ENDPOINTS.items() if path in opted}

def list_opted_endpoints(tenant_name: str) -> Optional[Dict[str, list]]:
    """The endpoints this workspace has opted into, by service code. None if the workspace is unknown."""
    tenant = cloud_sql_maas.get_tenant_by_name(tenant_name)
    if tenant is None:
        return None
    opted = endpoint_registry.enabled_paths(tenant["tenant_id"])
    result: Dict[str, list] = {code: [] for code in SERVICE_ORDER}
    for e in endpoint_registry.list_endpoints():
        if e["path"] in opted and not e["owner_side"]:
            result[e["service"]].append({k: e[k] for k in ("path", "service", "feature", "sub_category", "version", "actor", "category",
                                                           "description", "method", "ai", "parameters", "depends_on")})
    return result
