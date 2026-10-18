"""
Google Maps - Places API (new).
Address suggestions as a person types, and the details of the place they pick, for the delivery address form.

Send the same session_token for one whole typing session (every suggestion call and the final details call), so
Google bills the session once and not each keystroke.
"""

from typing import Any, Dict, List, Optional

from maps import client

AUTOCOMPLETE = "https://places.googleapis.com/v1/places:autocomplete"
DETAILS = "https://places.googleapis.com/v1/places/"

def autocomplete(text: str, session_token: Optional[str] = None, region: Optional[str] = None,
                 near: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
    """Suggestions for what the person is typing. Returns a short list of {place_id, text}."""
    if len(text.strip()) < 3:
        return []  # too short to be worth a billed call
    body: Dict[str, Any] = {"input": text}
    if session_token:
        body["sessionToken"] = session_token
    if region:
        body["includedRegionCodes"] = [region]
    if near:
        body["locationBias"] = {"circle": {"center": {"latitude": near["lat"], "longitude": near["lng"]}, "radius": 50000.0}}
    answer = client.post("Places", AUTOCOMPLETE, body)
    return [{"place_id": s["placePrediction"]["placeId"], "text": s["placePrediction"]["text"]["text"]}
            for s in answer.get("suggestions", []) if "placePrediction" in s]

def details(place_id: str, session_token: Optional[str] = None) -> Dict[str, Any]:
    """The address and coordinates of a place the person picked."""
    params = {"sessionToken": session_token} if session_token else None
    found = client.get("Places", DETAILS + place_id, params, "id,formattedAddress,location")
    where = found.get("location", {})
    return {"place_id": found.get("id"), "address": found.get("formattedAddress"),
            "lat": where.get("latitude"), "lng": where.get("longitude")}
