"""
Cloud Run - what the screens use from Google Maps.
Wraps the maps/ package so a screen never breaks because Maps is off: with no server key, or after the daily safety cap,
each call falls back to a straight-line estimate and says so (source: "estimate"). Every real call counts against the
daily cap in maps/client.py, which is the guard that keeps Maps inside the spend limit.
"""

import logging
import math
from typing import Any, Dict, List, Optional

import maps

log = logging.getLogger("lakshmi.maps")

BROAD_PLACES = {"country", "administrative_area_level_1", "administrative_area_level_2", "political"}
ROAD_FACTOR = 1.3     # straight line to road distance, a common rule of thumb
AVERAGE_KMH = 40      # for the estimate only

def haversine_km(a: Dict[str, float], b: Dict[str, float]) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, (a["lat"], a["lng"], b["lat"], b["lng"]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))

def _place(value: Any) -> Any:
    """A place as the Routes client wants it: an address string or a {lat, lng} point. Accepts {address} or {lat|latitude, lng|longitude}."""
    if isinstance(value, str):
        return value.strip()
    if not isinstance(value, dict):
        raise ValueError("A place must be an address or a point with latitude and longitude.")
    if value.get("address"):
        return str(value["address"]).strip()
    lat = value.get("lat", value.get("latitude"))
    lng = value.get("lng", value.get("longitude"))
    if lat is None or lng is None:
        raise ValueError("A place needs an address, or both latitude and longitude.")
    return {"lat": float(lat), "lng": float(lng)}

def road_route(origin: Any, destination: Any, mode: str = "DRIVE") -> Dict[str, Any]:
    """Road distance, time and the route line between two places. Falls back to a straight-line estimate (no line) for points."""
    start, end = _place(origin), _place(destination)
    try:
        return {**maps.routes.compute_route(start, end, mode=mode), "source": "Google Maps"}
    except maps.MapsError as problem:
        log.warning("Routes unavailable, estimating: %s", problem)
    if isinstance(start, dict) and isinstance(end, dict):
        km = haversine_km(start, end) * ROAD_FACTOR
        return {"distance_km": round(km, 1), "duration_minutes": round(km / AVERAGE_KMH * 60), "polyline": None, "mode": mode, "traffic": False,
                "source": "estimate"}
    raise ValueError("The route could not be worked out just now. Try again in a moment.")

def check_address(address: Dict[str, Any], country: str) -> Dict[str, Any]:
    """Whether an address exists, and where. address may hold line1, city, postcode, state or one free-text address."""
    text = address.get("address") or ", ".join(str(address[k]) for k in ("line1", "line2", "city", "state", "postcode") if address.get(k))
    if not text.strip():
        raise ValueError("Give an address to check.")
    code = country.strip().lower() if len(country.strip()) == 2 else None
    try:
        # a two-letter country code is a hard filter; a country written out in words is added to the text instead
        found = maps.geocoding.geocode(text if code else f"{text}, {country}", region=code, country=code)
    except maps.MapsError as problem:
        log.warning("Geocoding unavailable: %s", problem)
        return {"valid": None, "source": "not checked", "message": "Address checking is not available right now."}
    # Google answers an unknown address with the nearest place it knows, often just the country or a state: that is not an address
    too_broad = bool(found) and set(found["types"]) <= BROAD_PLACES
    if found is None or too_broad:
        return {"valid": False, "source": "Google Maps", "message": "That address was not found. Check the street, city and postcode."}
    return {"valid": True, "exact": found["exact"], "formatted_address": found["address"], "lat": found["lat"], "lng": found["lng"],
            "source": "Google Maps", "message": "Address found." if found["exact"] else "Address found, but only approximately."}

def stores_by_distance(lat: float, lng: float, stores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The stores with their distance from a point, nearest first. Road distance from Maps when available, else a straight-line estimate."""
    here = {"lat": lat, "lng": lng}
    located = [s for s in stores if s.get("latitude") is not None and s.get("longitude") is not None]
    out = [{**s, "distance_km": round(haversine_km(here, {"lat": s["latitude"], "lng": s["longitude"]}) * ROAD_FACTOR, 1), "distance_source": "estimate"} for s in located]
    if out:
        try:
            cells = maps.routes.route_matrix([here], [{"lat": s["latitude"], "lng": s["longitude"]} for s in located])
            for c in cells:
                if c["distance_km"] is not None and c["condition"] in (None, "ROUTE_EXISTS"):
                    out[c["destination"]].update(distance_km=c["distance_km"], duration_minutes=c["duration_minutes"], distance_source="Google Maps")
        except maps.MapsError as problem:
            log.warning("Route matrix unavailable, using estimates: %s", problem)
    out.sort(key=lambda s: s["distance_km"])
    return out
