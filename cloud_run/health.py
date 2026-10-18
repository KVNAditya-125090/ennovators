"""
Cloud Run - endpoint health
How every catalog endpoint is doing, from the calls the gate actually handled (the audit log), not a fixed list.

Each endpoint is in one of four states:
  working    it has a handler, and its recent calls did not fail on the server
  slow       its recent calls answered, but the slowest 5% took longer than SLOW_MS
  failing    one of its recent calls failed on the server (5xx, other than 501)
  not_built  no handler yet: the gate answers 501 (Customer features today)
Owner-side endpoints run through the Owner console (preview), so they count as working.
The audit log is in Cloud SQL (the last 7 days are read here); for long history read it from BigQuery.
"""

from typing import Any, Dict, List

from cloud_run.handlers import HANDLERS
from cloud_sql.services.maas.endpoints import endpoint_registry

SLOW_MS = 1500
RECENT = 20  # calls per endpoint looked at

def _p95(values: List[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]

def endpoint_health() -> Dict[str, Dict[str, Any]]:
    """{path: {state, calls, server_errors, p95_ms, last_status, last_at}} for every catalog endpoint."""
    recent = endpoint_registry.recent_calls(RECENT)  # newest first
    out = {}
    for e in endpoint_registry.list_endpoints():
        calls = recent.get(e["path"], [])
        built = e["owner_side"] or e["path"] in HANDLERS
        errors = sum(1 for c in calls if c["status"] >= 500 and c["status"] != 501)
        p95 = round(_p95([c["ms"] for c in calls if c.get("ms") is not None]), 1)
        state = "not_built" if not built else "failing" if errors else "slow" if p95 > SLOW_MS else "working"
        out[e["path"]] = {"state": state, "calls": len(calls), "server_errors": errors, "p95_ms": p95,
                          "last_status": calls[0]["status"] if calls else None, "last_at": calls[0]["at"] if calls else None}
    return out

def health_summary() -> Dict[str, Any]:
    """The figures for the Owner dashboard's Health card."""
    states = [h["state"] for h in endpoint_health().values()]
    day = endpoint_registry.calls_since(24)
    return {
        "endpoints_total": len(states),
        "endpoints_working": states.count("working"),
        "endpoints_slow": states.count("slow"),
        "endpoints_failing": states.count("failing"),
        "endpoints_not_built": states.count("not_built"),
        "calls_24h": day["total"],
        "success_rate_24h": round(100 * day["served"] / day["total"], 1) if day["total"] else None,
    }
