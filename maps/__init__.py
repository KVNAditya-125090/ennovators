"""
Google Maps - everything the backend needs from Maps, in one place.

    client      the shared caller: key, timeout, errors and the daily safety cap
    routes      Routes API: road distance, time and route line (TaaS delivery planning)
    geocoding   Geocoding API: address to coordinates and back
    places      Places API: address suggestions and place details

The browser side (the map and the address box) is in firebase_hosting/src/maps/.
"""

from maps import client, geocoding, places, routes  # noqa: F401
from maps.client import MapsError, MapsLimitReached, MapsNotConfigured  # noqa: F401
