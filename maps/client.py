"""
Google Maps - shared client.
Every call to a Maps API goes through here, so the key, the timeout, the errors and the daily safety cap live in one place.

Settings (environment variables):
    MAPS_SERVER_KEY    the server key, restricted to the Routes and Geocoding APIs. On Cloud Run it comes from Secret Manager.
    MAPS_DAILY_LIMIT   most calls one process makes to one API in a day (default 300). A second guard under the quota
                       set in Google Cloud: it stops a loop in our own code before it can cost anything.

Maps has no default spending cap, so never remove the daily limit.
"""

import datetime
import os
import threading
from typing import Any, Dict, Optional, Tuple

import httpx

TIMEOUT_SECONDS = 10.0
DEFAULT_DAILY_LIMIT = 300

class MapsError(Exception):
    """A Maps call failed. The message is safe to show."""

class MapsNotConfigured(MapsError):
    """No server key is set, so Maps cannot be used."""

class MapsLimitReached(MapsError):
    """The daily safety cap for this API was reached."""

_counts: Dict[Tuple[str, datetime.date], int] = {}
_lock = threading.Lock()

def daily_limit() -> int:
    try:
        return int(os.environ.get("MAPS_DAILY_LIMIT", DEFAULT_DAILY_LIMIT))
    except ValueError:
        return DEFAULT_DAILY_LIMIT

def server_key() -> str:
    key = (os.environ.get("MAPS_SERVER_KEY") or "").strip()  # a key piped into Secret Manager from a terminal can carry a trailing newline
    if not key:
        raise MapsNotConfigured("Maps is not configured: MAPS_SERVER_KEY is not set.")
    return key

def _spend(api: str) -> None:
    """Counts one call against today's cap for this API, or raises when the cap is used up."""
    today = datetime.date.today()
    with _lock:
        for stale in [k for k in _counts if k[1] != today]:
            del _counts[stale]
        used = _counts.get((api, today), 0)
        if used >= daily_limit():
            raise MapsLimitReached(f"The daily limit of {daily_limit()} {api} calls is used up. Try again tomorrow.")
        _counts[(api, today)] = used + 1

def usage_today() -> Dict[str, int]:
    """Calls made today, by API (for this process only)."""
    today = datetime.date.today()
    with _lock:
        return {api: n for (api, day), n in _counts.items() if day == today}

def _send(api: str, method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
    key = server_key()
    _spend(api)
    headers = {"X-Goog-Api-Key": key, **kwargs.pop("headers", {})}
    try:
        response = httpx.request(method, url, headers=headers, timeout=TIMEOUT_SECONDS, **kwargs)
    except httpx.HTTPError as problem:
        raise MapsError(f"{api} could not be reached: {problem.__class__.__name__}") from None
    if response.status_code >= 400:
        try:
            reason = response.json().get("error", {}).get("message", "")
        except ValueError:
            reason = ""
        raise MapsError(f"{api} answered {response.status_code}. {reason}".strip())
    return response.json()

def post(api: str, url: str, body: Dict[str, Any], field_mask: Optional[str] = None) -> Dict[str, Any]:
    """POST to a Maps API. The field mask limits what comes back, which also keeps the call on the cheapest price tier."""
    headers = {"X-Goog-FieldMask": field_mask} if field_mask else {}
    return _send(api, "POST", url, json=body, headers=headers)

def get(api: str, url: str, params: Optional[Dict[str, Any]] = None, field_mask: Optional[str] = None) -> Dict[str, Any]:
    headers = {"X-Goog-FieldMask": field_mask} if field_mask else {}
    return _send(api, "GET", url, params=params, headers=headers)
