"""
Cloud Run - the gate
Every endpoint of the catalog is reachable at /api<catalog path>, for example /api/paas/catalog/product/read/v1.
Each call passes the same checks, in order, and fails closed:

    1. the caller names a known consumer         (401 / 404)
    2. the endpoint is one a consumer may call   (403 owner_side)
    3. the consumer has MaaS                     (403 maas_required)
    4. the consumer opted into the endpoint      (403 not_purchased)
    4b. the caller is named, belongs to the consumer and their role allows it   (401 / 403 role_not_allowed)
    5. the consumer is within the rate limit     (429 rate_limited)

Every call is written to the audit log, and every allowed call is counted for usage and cost. Handlers are not
built for every endpoint: a call with no handler answers 501 not_implemented (see handlers.py).

Preview limits: the consumer is named by the X-Tenant-Id header (there is no real sign-in yet), and the
rate-limit window, the call counts and the audit log live in this process's memory.
"""

import time
from collections import deque
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request, Response

from bigquery.services.maas import bigquery_maas
from cloud_sql.services.maas import cloud_sql_maas
from urllib.parse import unquote

from cloud_run.access import allowed_paths
from cloud_run.handlers import HANDLERS
from firestore.users.consumer import operations as consumer_ops
from cloud_sql.services.maas.endpoints import endpoint_registry

router = APIRouter(prefix="/api", tags=["Gate"])

WINDOW_SECONDS = 60
_window: Dict[tuple, deque] = {}  # (tenant_id, path) -> times of the allowed calls in the last minute

def _refuse(status: int, code: str, message: str, headers: Optional[Dict[str, str]] = None) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message}, headers=headers)

def _check(tenant_id: Optional[str], endpoint: Dict[str, Any], user_email: Optional[str] = None) -> Dict[str, Any]:
    """Runs the gate. Returns the tenant, or raises the refusal."""
    if not tenant_id:
        raise _refuse(401, "unauthenticated", "Say which consumer is calling with the X-Tenant-Id header.")
    tenant = cloud_sql_maas.get_tenant(tenant_id)
    if tenant is None:
        raise _refuse(404, "unknown_consumer", "This consumer does not exist.")
    if endpoint["owner_side"]:
        raise _refuse(403, "owner_side", "This endpoint runs on the Owner side. A consumer cannot call it.")
    opted = endpoint_registry.enabled_paths(tenant_id)
    if not opted & {e["path"] for e in endpoint_registry.list_endpoints("MaaS") if not e["owner_side"]}:
        raise _refuse(403, "maas_required", "MaaS is required for every consumer.")
    if endpoint["path"] not in opted:
        raise _refuse(403, "not_purchased", "This consumer has not opted into this endpoint.")
    if not user_email:
        raise _refuse(401, "unauthenticated", "Say who is calling with the X-User-Email header.")
    allowed = allowed_paths(user_email, tenant["name"])
    if allowed is not None and endpoint["path"] not in allowed:
        raise _refuse(403, "role_not_allowed", "Your role is not allowed to use this feature.")

    limit = endpoint_registry.endpoint_settings(tenant_id)[endpoint["path"]]["rate_limit_per_min"]
    calls = _window.setdefault((tenant_id, endpoint["path"]), deque())
    now = time.monotonic()
    while calls and now - calls[0] >= WINDOW_SECONDS:
        calls.popleft()
    if len(calls) >= limit:
        wait = max(1, int(WINDOW_SECONDS - (now - calls[0])) + 1)
        raise _refuse(429, "rate_limited", f"Over the limit of {limit} calls per minute. Try again in {wait} seconds.",
                      {"Retry-After": str(wait)})
    calls.append(now)
    return tenant

def _params(request: Request, body: Any) -> Dict[str, Any]:
    if endpoint_is_read(request.method):
        return dict(request.query_params)
    return body if isinstance(body, dict) else {}

def endpoint_is_read(method: str) -> bool:
    return method in ("GET", "DELETE")

NUMBER_TYPES = {"int": int, "num": float}

def _coerce(endpoint: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """Query strings arrive as text: turn numbers into numbers, and refuse a value the endpoint does not accept."""
    out = dict(params)
    for p in endpoint["parameters"]:
        value = out.get(p["name"])
        if value in (None, ""):
            continue
        try:
            if p["type"] in NUMBER_TYPES:
                out[p["name"]] = NUMBER_TYPES[p["type"]](value)
        except (TypeError, ValueError):
            raise _refuse(422, "invalid_request", f"{p['name']} must be a number")
        if p["type"] == "enum" and value not in p["values"]:
            raise _refuse(422, "invalid_request", f"{p['name']} must be one of: " + ", ".join(p["values"]))
    return out

def _missing(endpoint: Dict[str, Any], params: Dict[str, Any]) -> list:
    return [p["name"] for p in endpoint["parameters"] if p["required"] and params.get(p["name"]) in (None, "", [])]

def _handler(endpoint: Dict[str, Any]):
    async def call(request: Request, response: Response, x_tenant_id: Optional[str] = Header(None), x_user_name: Optional[str] = Header(None), x_user_email: Optional[str] = Header(None)):
        try:
            tenant = _check(x_tenant_id, endpoint, unquote(x_user_email) if x_user_email else None)
        except HTTPException as refusal:
            endpoint_registry.record_audit(x_tenant_id, endpoint["path"], endpoint["method"], refusal.status_code, refusal.detail["code"])
            raise
        bigquery_maas.record_call(x_tenant_id, endpoint["path"])
        body = None
        if not endpoint_is_read(request.method):
            try:
                body = await request.json()
            except ValueError:
                body = None
        try:
            params = _coerce(endpoint, _params(request, body))
        except HTTPException:
            endpoint_registry.record_audit(x_tenant_id, endpoint["path"], endpoint["method"], 422, "invalid_request")
            raise
        missing = _missing(endpoint, params)
        if missing:
            endpoint_registry.record_audit(x_tenant_id, endpoint["path"], endpoint["method"], 422, "invalid_request")
            raise _refuse(422, "invalid_request", "Missing required parameters: " + ", ".join(missing))
        handler = HANDLERS.get(endpoint["path"])
        if handler is None:
            endpoint_registry.record_audit(x_tenant_id, endpoint["path"], endpoint["method"], 501, "not_implemented")
            raise _refuse(501, "not_implemented", "This endpoint passed the gate, but its handler is not built yet.")
        started = time.monotonic()
        took = lambda: round((time.monotonic() - started) * 1000, 1)
        try:
            consumer_ops.ACTOR.set(unquote(x_user_name).strip() or None if x_user_name else None)
            result = handler(tenant, params)
        except LookupError as err:
            endpoint_registry.record_audit(x_tenant_id, endpoint["path"], endpoint["method"], 404, "not_found", took())
            raise _refuse(404, "not_found", str(err).strip("'\""))
        except ValueError as err:
            endpoint_registry.record_audit(x_tenant_id, endpoint["path"], endpoint["method"], 422, "refused", took())
            raise _refuse(422, "refused", str(err))
        except Exception:
            endpoint_registry.record_audit(x_tenant_id, endpoint["path"], endpoint["method"], 500, "server_error", took())
            raise _refuse(500, "server_error", "Something went wrong on our side. Please try again.")
        endpoint_registry.record_audit(x_tenant_id, endpoint["path"], endpoint["method"], 200, "ok", took())
        return result
    call.__name__ = "call_" + endpoint["path"].strip("/").replace("/", "_").replace("-", "_")
    return call

for _endpoint in endpoint_registry.list_endpoints():
    router.add_api_route(
        _endpoint["path"], _handler(_endpoint), methods=[_endpoint["method"]],
        summary=_endpoint["description"], tags=[_endpoint["service"]],
        responses={403: {"description": "Not purchased, owner side or no MaaS"}, 429: {"description": "Over the rate limit"},
                   501: {"description": "Passed the gate; handler not built yet"}},
    )
