"""
BigQuery - PaaS (Product as a Service)
Daily sales fact table that feeds Vertex AI demand forecasting.
"""

from typing import Dict, Any, List
import random
import datetime

class BigQueryPaaS:
    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def get_demand_history(self, sku: str, days: int = 60) -> List[Dict[str, Any]]:
        """Simulates a SELECT over the daily sales fact table for one SKU."""
        today = datetime.date.today()
        base = random.randint(20, 50)
        return [
            {
                "date": (today - datetime.timedelta(days=days - i)).strftime("%Y-%m-%d"),
                "units_sold": max(0, base + random.randint(-8, 12))
            }
            for i in range(days)
        ]

bigquery_paas = BigQueryPaaS()
