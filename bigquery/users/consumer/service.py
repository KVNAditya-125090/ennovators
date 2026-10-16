"""
BigQuery - Consumer
What the Consumer reads: demand history for stock planning, and its workspace usage.
"""

from typing import Dict, Any, List
from bigquery.services.paas import bigquery_paas
from bigquery.services.maas import bigquery_maas

def get_demand_history(sku: str) -> List[Dict[str, Any]]:
    return bigquery_paas.get_demand_history(sku)

def get_workspace_usage(tenant_name: str) -> Dict[str, Any]:
    return bigquery_maas.get_workspace_usage(tenant_name)
