"""
Cloud SQL - Consumer
What the Consumer reads: its own tenant workspace and team, through Management as a Service.
"""

from typing import Dict, Any, Optional, Set
from cloud_sql.services.maas import cloud_sql_maas

def get_workspace(tenant_name: str) -> Optional[Dict[str, Any]]:
    return cloud_sql_maas.get_workspace(tenant_name)

def enabled_api_ids(tenant_name: str) -> Optional[Set[str]]:
    """The APIs the Owner has enabled for this workspace, or None if the workspace is unknown."""
    tenant = cloud_sql_maas.get_tenant_by_name(tenant_name)
    return None if tenant is None else cloud_sql_maas.enabled_api_ids(tenant["tenant_id"])
