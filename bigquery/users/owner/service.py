"""
BigQuery - Owner
What the Owner reads: spend against the budget cap, and each consumer's API usage.
"""

from typing import Dict, Any, List
from bigquery.services.maas import bigquery_maas

def get_budget_status() -> Dict[str, Any]:
    return bigquery_maas.get_budget_status()

def get_gcp_logs() -> List[Dict[str, Any]]:
    return bigquery_maas.get_gcp_logs()

def get_endpoint_usage(tenant_id: str, categories: Dict[str, str]) -> Dict[str, int]:
    return bigquery_maas.get_endpoint_usage(tenant_id, categories)

def get_workspace_usage(tenant_name: str) -> Dict[str, Any]:
    return bigquery_maas.get_workspace_usage(tenant_name)

def get_platform_history(period: str, month_revenue: float, month_hosting_cost: float, month_requests: int, consumer_count: int = 3) -> List[Dict[str, Any]]:
    return bigquery_maas.get_platform_history(period, month_revenue, month_hosting_cost, month_requests, consumer_count)

def get_hosting_plan() -> List[Dict[str, Any]]:
    return bigquery_maas.get_hosting_plan()
