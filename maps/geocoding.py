"""
Google Maps - Geocoding API.
Turns an address into coordinates (store lookup, delivery addresses) and coordinates back into an address.
"""

from typing import Any, Dict, Optional

from maps import client

GEOCODE = "https://maps.googleapis.com/maps/api/geocode/json"

def _first(answer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    status = answer.get("status")
    if status == "ZERO_RESULTS":
        return None
    if status != "OK":
        raise client.MapsError(f"Geocoding answered {status}. {answer.get('error_message', '')}".strip())
    top = answer["results"][0]
    where = top["geometry"]["location"]
    return {"address": top["formatted_address"], "lat": where["lat"], "lng": where["lng"], "place_id": top.get("place_id"),
            "exact": top["geometry"].get("location_type") in ("ROOFTOP", "RANGE_INTERPOLATED"),
            "types": top.get("types", []), "partial_match": bool(top.get("partial_match"))}

def geocode(address: str, region: Optional[str] = None, country: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """The coordinates of an address, or None when it is not found. region is a two-letter country code such as "in" that only
    biases the result; country is the same code used as a hard filter, so an address that exists only in another country is not found."""
    params: Dict[str, Any] = {"address": address, "key": client.server_key()}
    if region:
        params["region"] = region
    if country:
        params["components"] = f"country:{country.upper()}"
    return _first(client.get("Geocoding", GEOCODE, params))

def reverse_geocode(lat: float, lng: float) -> Optional[Dict[str, Any]]:
    """The address nearest to a point, or None."""
    return _first(client.get("Geocoding", GEOCODE, {"latlng": f"{lat},{lng}", "key": client.server_key()}))
