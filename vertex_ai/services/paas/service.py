"""
Vertex AI - PaaS (Product as a Service)
TimesFM zero-shot demand forecasting over BigQuery history (mock provider, keyless mode).
"""

from typing import Dict, Any, List
import random
import datetime

class VertexAIPaaS:
    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def predict_demand_timesfm(self, sku: str, history: List[Dict[str, Any]] = None, days: int = 14) -> List[Dict[str, Any]]:
        """Simulates TimesFM zero-shot time series forecast over BigQuery demand history."""
        today = datetime.date.today()
        if history:
            base = int(sum(h["units_sold"] for h in history) / len(history))
        else:
            base = random.randint(20, 50)
        forecast = []
        for i in range(days):
            date_str = (today + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            val = max(5, int(base + random.randint(-8, 15) + (i * 0.5)))
            forecast.append({
                "date": date_str,
                "predicted_demand": val,
                "lower_bound": max(0, val - 4),
                "upper_bound": val + 6
            })
        return forecast

vertex_paas = VertexAIPaaS()
