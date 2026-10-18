"""
Google Maps - Routes API (TaaS).
Road distance, travel time and the route line between places, for the delivery planner.
A place is either an address string or a point: {"lat": 18.52, "lng": 73.85}.

Traffic-aware routing is a higher-priced tier, so it is off unless asked for (traffic=True).
"""

from typing import Any, Dict, List, Optional, Union

from maps import client

Place = Union[str, Dict[str, float]]

COMPUTE_ROUTES = "https://routes.googleapis.com/directions/v2:computeRoutes"
ROUTE_MATRIX = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
TRAVEL_MODES = ("DRIVE", "TWO_WHEELER", "BICYCLE", "WALK", "TRANSIT")

def _waypoint(place: Place) -> Dict[str, Any]:
    if isinstance(place, str):
        return {"address": place}
    return {"location": {"latLng": {"latitude": float(place["lat"]), "longitude": float(place["lng"])}}}

def _seconds(duration: Optional[str]) -> Optional[int]:
    """Maps sends durations like "1234s"."""
    return int(duration.rstrip("s")) if duration else None

def compute_route(origin: Place, destination: Place, stops: Optional[List[Place]] = None, mode: str = "DRIVE",
                  traffic: bool = False, avoid_tolls: bool = False, avoid_highways: bool = False) -> Dict[str, Any]:
    """The best route from origin to destination through the stops. Returns distance, time and the route line."""
    if mode not in TRAVEL_MODES:
        raise client.MapsError(f"mode must be one of: {', '.join(TRAVEL_MODES)}")
    body: Dict[str, Any] = {"origin": _waypoint(origin), "destination": _waypoint(destination), "travelMode": mode}
    if stops:
        body["intermediates"] = [_waypoint(s) for s in stops]
    if mode in ("DRIVE", "TWO_WHEELER"):
        body["routingPreference"] = "TRAFFIC_AWARE" if traffic else "TRAFFIC_UNAWARE"
    if mode == "DRIVE" and (avoid_tolls or avoid_highways):
        body["routeModifiers"] = {"avoidTolls": avoid_tolls, "avoidHighways": avoid_highways}
    mask = "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline"
    found = client.post("Routes", COMPUTE_ROUTES, body, mask).get("routes", [])
    if not found:
        raise client.MapsError("No route was found between these places.")
    route = found[0]
    return {"distance_km": round(route["distanceMeters"] / 1000, 1), "duration_minutes": round(_seconds(route["duration"]) / 60),
            "polyline": route.get("polyline", {}).get("encodedPolyline"), "mode": mode, "traffic": traffic}

def route_matrix(origins: List[Place], destinations: List[Place], mode: str = "DRIVE") -> List[Dict[str, Any]]:
    """Distance and time for every origin and destination pair (one billed element per pair)."""
    if len(origins) * len(destinations) > 100:
        raise client.MapsError("Ask for at most 100 origin and destination pairs at once.")
    body = {"origins": [{"waypoint": _waypoint(o)} for o in origins], "destinations": [{"waypoint": _waypoint(d)} for d in destinations],
            "travelMode": mode}
    mask = "originIndex,destinationIndex,distanceMeters,duration,condition"
    # the matrix answers as a stream of JSON objects in a list
    answer = client.post("Routes", ROUTE_MATRIX, body, mask)
    items = answer if isinstance(answer, list) else [answer]
    return [{"origin": i.get("originIndex", 0), "destination": i.get("destinationIndex", 0), "condition": i.get("condition"),
             "distance_km": round(i["distanceMeters"] / 1000, 1) if "distanceMeters" in i else None,
             "duration_minutes": round(_seconds(i["duration"]) / 60) if i.get("duration") else None} for i in items]
