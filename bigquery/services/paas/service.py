"""
BigQuery - PaaS (Product as a Service)
The daily sales table (sales_daily: day, sku, units) that feeds the demand forecast.
"""

import logging
from typing import Dict, Any, List

from bigquery.services.maas import DATASET, PROJECT, cached, query

log = logging.getLogger("lakshmi.bigquery")

class BigQueryPaaS:
    def __init__(self):
        self.provider_status = "BigQuery"

    def get_demand_history(self, sku: str, days: int = 60) -> List[Dict[str, Any]]:
        """Units sold each day of the last days for one SKU, oldest first. Empty when no sales have been loaded."""
        def make():
            try:
                return [{"date": r["date"], "units_sold": int(r["units_sold"])} for r in query(
                    f"SELECT CAST(day AS STRING) AS date, units AS units_sold FROM `{PROJECT}.{DATASET}.sales_daily` "
                    "WHERE sku = @sku AND day >= DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY) ORDER BY day", sku=sku, days=days)]
            except Exception:
                log.exception("could not read the sales history")
                return []
        return cached(f"sales:{sku}:{days}", 120, make) if sku else []

bigquery_paas = BigQueryPaaS()
