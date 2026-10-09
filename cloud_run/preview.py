"""
Cloud Run - preview handlers
Stand-ins for the Owner and Consumer features whose real handler is not built yet, so every one of them can be used
from the interface today. A change is recorded (who, when, what was sent) and a read returns what was recorded for
that feature. Nothing else happens: no mail is sent, no money moves, no session is created.

To integrate a feature with the real backend, write its handler in handlers.py (or the Owner router). A real
handler always wins: previews are registered only for paths that have none. Every preview answer carries
"preview": true, so the interface can say the result is not real yet.
State is in memory, like the rest of the preview.
"""

import datetime
import itertools
from typing import Any, Callable, Dict, List, Optional

from cloud_sql.services.maas.endpoints import endpoint_registry
from firestore.users.consumer import operations as ops

# People, plus the automatic jobs, AI services and partner actions that work on a consumer's data (run on demand in the preview)
PREVIEW_ACTORS = {"Consumer root", "Consumer staff", "Owner manager", "Owner operator", "Owner developer", "System", "AI", "Partner"}
STORE: Dict[tuple, List[Dict[str, Any]]] = {}  # (scope, service, feature) -> records, newest first
_ids = itertools.count(1)

def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")

def _mask(endpoint: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """Passwords, tokens and other secrets are never kept or echoed."""
    secret = {p["name"] for p in endpoint["parameters"] if p["type"] == "secret"}
    return {k: ("••••••" if k in secret else v) for k, v in params.items()}

def run(scope: str, endpoint: Dict[str, Any], params: Dict[str, Any], actor: Optional[str] = None) -> Dict[str, Any]:
    """scope: the consumer's tenant id, or "owner" for the Owner side."""
    key = (scope, endpoint["service"], endpoint["feature"])
    if endpoint["method"] == "GET":
        items = [r for r in STORE.get(key, []) if all(str(r["params"].get(k)) == str(v) for k, v in params.items() if v not in (None, "") and k in r["params"])]
        return {"preview": True, "items": items,
                "note": "Preview: shows what was recorded for this feature in this session. Real data arrives once the backend is connected."}
    record = {"id": f"pv-{next(_ids)}", "action": endpoint["sub_category"].replace("/", " "), "endpoint": endpoint["path"],
              "params": _mask(endpoint, params), "at": _now(), "by": actor or ops.ACTOR.get() or "", "status": "recorded"}
    STORE.setdefault(key, []).insert(0, record)
    return {"preview": True, "record": record,
            "message": f"{endpoint['description']}: recorded in the preview. It takes effect once the backend is connected."}

def register_previews(handlers: Dict[str, Callable]) -> int:
    """Give every Consumer feature with no real handler a preview one. Owner features go through the Owner router."""
    added = 0
    for e in endpoint_registry.list_endpoints():
        if e["owner_side"] or e["actor"] not in PREVIEW_ACTORS or e["path"] in handlers:
            continue
        handlers[e["path"]] = lambda tenant, params, e=e: run(tenant["tenant_id"], e, params)
        added += 1
    return added
