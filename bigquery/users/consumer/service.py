"""
BigQuery - Consumer
What the Consumer reads: demand history used for stock planning.
"""

from typing import Dict, Any, List
from bigquery.services.paas import bigquery_paas

def get_demand_history(sku: str) -> List[Dict[str, Any]]:
    return bigquery_paas.get_demand_history(sku)
