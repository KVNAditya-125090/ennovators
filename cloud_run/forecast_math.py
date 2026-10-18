"""
Cloud Run - when to reorder.
The reorder point is the stock level at which new stock must be ordered so it arrives before the shelf is empty: the units
expected to sell while the new stock is on its way, plus a safety margin for a busier-than-expected week.
It is worked out from the forecast the page already shows and the real sales history, so it changes when they do.
"""

import math
import statistics
from typing import Any, Dict, List

LEAD_TIME_DAYS = 7      # how long new stock takes to arrive (an assumption, shown to the person in the explanation)
SERVICE_FACTOR = 1.65   # covers a normal week about 95 times in 100

def _daily(days: List[Dict[str, Any]]) -> float:
    shown = days[:14]
    return sum(d["predicted_demand"] for d in shown) / len(shown) if shown else 0.0

def _margin(history: List[Dict[str, Any]], daily: float) -> float:
    sold = [h["units_sold"] for h in history]
    spread = statistics.pstdev(sold) if len(sold) > 1 else daily * 0.3
    return SERVICE_FACTOR * spread * math.sqrt(LEAD_TIME_DAYS)

def reorder_point(history: List[Dict[str, Any]], days: List[Dict[str, Any]]) -> int:
    """Units of stock at which to reorder. 0 only when there is no forecast at all."""
    daily = _daily(days)
    if not days or daily <= 0:
        return 0
    return max(1, math.ceil(daily * LEAD_TIME_DAYS + _margin(history, daily)))

def describe(history: List[Dict[str, Any]], days: List[Dict[str, Any]], point: int) -> str:
    daily = _daily(days)
    while_waiting = round(daily * LEAD_TIME_DAYS)
    return (f"Reorder when stock reaches {point} units: about {while_waiting} units sell while new stock arrives "
            f"(assuming {LEAD_TIME_DAYS} days), plus a safety margin of {max(point - while_waiting, 0)} for a busier week.")
