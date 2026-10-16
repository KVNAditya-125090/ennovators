"""
Cloud Run - keeping the three portals in step.
Anything that changes what a person may see or do (the Owner opting a consumer in or out, a consumer's roles,
role permissions, team, interface template or role views) bumps one counter. Each portal asks for the counter every few
seconds and reloads what it shows when it moved, so an Owner's switch reaches the Consumer console and the Customer
storefront without anyone signing in again.
Preview limit: the counter lives in this process's memory, like the rest of the preview data.
"""

from fastapi import APIRouter, FastAPI, Request

router = APIRouter(prefix="/api/v1/sync", tags=["Sync"])

_revision = {"n": 0}

# Paths whose successful changes can alter access or the interface. Shopper actions (cart, bids, tickets, account) do not.
_AFFECTS_ACCESS = ("/api/v1/owner", "/api/maas/")
_SHOPPER = ("/api/maas/customer-account", "/api/maas/locale", "/api/maas/assistant", "/api/maas/location")

def bump() -> int:
    _revision["n"] += 1
    return _revision["n"]

def current() -> int:
    return _revision["n"]

@router.get("/revision")
def get_revision() -> dict:
    return {"revision": _revision["n"]}

def install(app: FastAPI) -> None:
    """Counts every successful change that can alter access or the interface."""
    @app.middleware("http")
    async def _count_changes(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if (request.method in ("POST", "PUT", "PATCH", "DELETE") and response.status_code < 400
                and path.startswith(_AFFECTS_ACCESS) and not path.startswith(_SHOPPER)):
            bump()
        return response
