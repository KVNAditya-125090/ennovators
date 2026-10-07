"""
BigQuery - Owner
What the Owner reads: spend against the budget cap.
"""

from typing import Dict, Any
from bigquery.services.maas import bigquery_maas

def get_budget_status() -> Dict[str, Any]:
    return bigquery_maas.get_budget_status()
