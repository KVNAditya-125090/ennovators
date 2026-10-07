"""
Vertex AI - Consumer
What the Consumer uses: demand forecasting for stock planning.
"""

from typing import Dict, Any, List
from vertex_ai.services.paas import vertex_paas

def forecast_demand(sku: str, history: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    return vertex_paas.predict_demand_timesfm(sku, history)
