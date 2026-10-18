"""
Firestore - the store.
A small unit of work over Firestore, so the handlers can keep working on plain lists and dicts.

During one request:
  * the first time a collection is asked for it is read from Firestore, and the same list comes back every time after;
  * when the request ends well (status below 400) only what changed is written back, in one batch;
  * when it ends badly nothing is written.

What is written is the FIELDS that changed, not the whole record. So when two people change different fields of the same
record at about the same time (one the price, the other the stock) both changes are kept. Only when both change the very same
field does the later save win. A new record is written whole.

Where things live:
  tenants/{tenant id}/{name}/{doc id}   a consumer's own records (products, orders, shipments, shopper data...)
  {name}/{doc id}                       platform-wide records (visitor queries, tickets raised with the Owner)

A request names its consumer with set_tenant(): the gate does it for every catalog call. Asking for a consumer's records
with no consumer set is an error, so one consumer's data can never be read by mistake as another's.

Each record is stored as the plain dict the handlers already use. The order of a list is kept by a hidden time stamp.
Settings: GCP_PROJECT (default ennovators).
"""

import contextvars
import copy
import json
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger("lakshmi.store")

_client = None
_client_lock = threading.Lock()

def client():
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                from google.cloud import firestore
                _client = firestore.Client(project=os.environ.get("GCP_PROJECT", "ennovators"))
    return _client

def _delete_field():
    from google.cloud import firestore
    return firestore.DELETE_FIELD

def _fingerprint(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)

def _clean(value: Any) -> Any:
    """What Firestore can hold: tuples and sets become lists, and a value it cannot hold is refused here, with a clear message."""
    return json.loads(json.dumps(value, default=lambda o: sorted(o) if isinstance(o, set) else str(o)))

def _diff(before: Dict[str, Any], after: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """The fields of a record that changed since it was loaded: ({field: new value}, [fields that were removed])."""
    now = _clean(after)
    changed = {k: v for k, v in now.items() if k not in before or _fingerprint(before[k]) != _fingerprint(v)}
    removed = [k for k in before if k not in now]
    return changed, removed

class _Table:
    def __init__(self, path: str, key: str, newest_first: bool):
        self.path, self.key, self.newest_first = path, key, newest_first
        self.rows: List[Dict[str, Any]] = []
        self.before: Dict[str, Dict[str, Any]] = {}   # doc id -> the record as it was when loaded
        self.stamps: Dict[str, int] = {}              # doc id -> hidden time stamp

class _Doc:
    def __init__(self, path: str, data: Dict[str, Any], existed: bool):
        self.path, self.data, self.existed = path, data, existed
        self.before: Dict[str, Any] = copy.deepcopy(_clean(data))   # as loaded (or the default, for a new document)
        self.deleted = False

class Session:
    def __init__(self) -> None:
        self.tenant: Optional[str] = None
        self.tables: Dict[str, _Table] = {}
        self.docs: Dict[str, _Doc] = {}

    def _base(self, scope: str, tenant_id: Optional[str]) -> str:
        if scope == "global":
            return ""
        tenant = tenant_id or self.tenant
        if not tenant:
            raise RuntimeError("No consumer is set for this request, so its records cannot be read or written")
        return f"tenants/{tenant}/"

    # ---- lists of records ----
    def rows(self, name: str, key: str, scope: str = "tenant", newest_first: bool = False, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        path = self._base(scope, tenant_id) + name
        table = self.tables.get(path)
        if table is None:
            table = self.tables[path] = _Table(path, key, newest_first)
            loaded = []
            for snap in client().collection(path).stream():
                data = snap.to_dict() or {}
                stamp = int(data.pop("_ts", 0))
                table.before[snap.id] = copy.deepcopy(data)
                table.stamps[snap.id] = stamp
                loaded.append((stamp, data))
            loaded.sort(key=lambda pair: pair[0], reverse=newest_first)
            table.rows = [data for _, data in loaded]
        return table.rows

    # ---- one document by name ----
    def kdoc(self, name: str, doc_id: str, default: Callable[[], Dict[str, Any]], scope: str = "tenant", tenant_id: Optional[str] = None) -> Dict[str, Any]:
        path = f"{self._base(scope, tenant_id)}{name}/{doc_id.replace('/', '_')}"
        doc = self.docs.get(path)
        if doc is None:
            snap = client().document(path).get()
            doc = _Doc(path, snap.to_dict() or {}, True) if snap.exists else _Doc(path, default(), False)
            self.docs[path] = doc
        return doc.data

    def drop(self, name: str, doc_id: str, scope: str = "tenant", tenant_id: Optional[str] = None) -> None:
        """Deletes a named document when the request ends well."""
        self.kdoc(name, doc_id, dict, scope=scope, tenant_id=tenant_id)
        self.docs[f"{self._base(scope, tenant_id)}{name}/{doc_id.replace('/', '_')}"].deleted = True

    # ---- writing back ----
    def flush(self) -> int:
        """Writes what changed. Returns how many documents were written or deleted."""
        writes: List[Tuple[str, str, Any]] = []   # (action, path, data); action is set, update or delete
        for table in self.tables.values():
            seen = set()
            for row in table.rows:
                doc_id = str(row[table.key])
                seen.add(doc_id)
                path = f"{table.path}/{doc_id}"
                before = table.before.get(doc_id)
                if before is None:                                      # a new record: written whole
                    stamp = table.stamps.get(doc_id) or time.time_ns()
                    table.stamps[doc_id] = stamp
                    writes.append(("set", path, {**_clean(row), "_ts": stamp}))
                else:                                                   # an existing one: only the fields that changed
                    changed, removed = _diff(before, row)
                    if changed or removed:
                        writes.append(("update", path, {**changed, **{k: _delete_field() for k in removed}}))
                table.before[doc_id] = copy.deepcopy(_clean(row))
            for doc_id in set(table.before) - seen:
                writes.append(("delete", f"{table.path}/{doc_id}", None))
                del table.before[doc_id]
        for doc in self.docs.values():
            if doc.deleted:
                if doc.existed:
                    writes.append(("delete", doc.path, None))
                    doc.existed = False
                continue
            changed, removed = _diff(doc.before, doc.data)
            if not (changed or removed):
                continue
            if doc.existed:
                writes.append(("update", doc.path, {**changed, **{k: _delete_field() for k in removed}}))
            else:
                writes.append(("set", doc.path, _clean(doc.data)))
            doc.before, doc.existed = copy.deepcopy(_clean(doc.data)), True
        if not writes:
            return 0
        db = client()
        for start in range(0, len(writes), 400):  # a batch holds at most 500 writes
            batch = db.batch()
            for action, path, data in writes[start:start + 400]:
                ref = db.document(path)
                if action == "set":
                    batch.set(ref, data)
                elif action == "update":
                    batch.update(ref, data)
                else:
                    batch.delete(ref)
            batch.commit()
        return len(writes)

_session: contextvars.ContextVar = contextvars.ContextVar("store_session", default=None)

def begin() -> contextvars.Token:
    """Starts the unit of work for one request (or one script)."""
    return _session.set(Session())

def end(token: contextvars.Token) -> None:
    _session.reset(token)

def session() -> Session:
    current = _session.get()
    if current is None:
        raise RuntimeError("No store session: the request did not start one")
    return current

def set_tenant(tenant_id: Optional[str]) -> None:
    session().tenant = tenant_id

def flush() -> int:
    return session().flush()

def rows(name: str, key: str, **options: Any) -> List[Dict[str, Any]]:
    return session().rows(name, key, **options)

def kdoc(name: str, doc_id: str, default: Callable[[], Dict[str, Any]], **options: Any) -> Dict[str, Any]:
    return session().kdoc(name, doc_id, default, **options)

def drop(name: str, doc_id: str, **options: Any) -> None:
    session().drop(name, doc_id, **options)

class KeyedDict:
    """A dict whose entries are documents, so existing code that uses `DECISIONS[id]`, `in` and `pop` keeps working."""

    def __init__(self, name: str):
        self.name = name

    def __contains__(self, key: str) -> bool:
        return bool(self.get(key))

    def get(self, key: str, default: Any = None) -> Any:
        doc = kdoc(self.name, key, dict)
        return doc.get("value", default) if doc else default

    def __getitem__(self, key: str) -> Any:
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        doc = kdoc(self.name, key, dict)
        doc.clear()
        doc["value"] = value

    def pop(self, key: str, default: Any = None) -> Any:
        doc = kdoc(self.name, key, dict)
        value = doc.pop("value", default)
        doc.clear()
        return value
