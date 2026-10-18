"""
Cloud Run - one unit of work per request.
Opens the Firestore store before the request runs, and writes the changes back when it ends with a status below 400.
A request that fails writes nothing, so a refused or half-finished change never reaches the database.
If the write itself fails, the caller gets a 500 and is told nothing was saved.
"""

import logging

from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from firestore import store

log = logging.getLogger("lakshmi.unit_of_work")

class UnitOfWorkMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        token = store.begin()
        try:
            response = await call_next(request)
            if response.status_code < 400:
                try:
                    await run_in_threadpool(store.flush)
                except Exception:
                    log.exception("could not write the changes to Firestore")
                    return JSONResponse(status_code=500, content={"detail": {"code": "storage_failed", "message": "Your change could not be saved. Nothing was changed."}})
            return response
        finally:
            store.end(token)
