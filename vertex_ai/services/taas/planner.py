"""
Vertex AI - TaaS delivery planner (preview model)
AI recommendations for a shipment, each with a plain-language explanation:
  - route:   shortest, fastest, cheapest or greenest path, across one or more stops
  - vehicle: which vehicle type fits the load and distance best
  - eta:     the predicted delivery date and time, with a window and confidence
  - slot:    delivery slots ranked by how likely they are to be on time
Staff accept a recommendation, or override it with a reason; either way it is applied to the shipment and kept.

PREVIEW: this is a transparent rule-based stand-in so the interface works end to end. Distances are straight-line
between known city centres times a road factor; speeds, costs and emissions are typical figures, not live data.
Replace with the real model (Vertex AI, maps and traffic data) when the backend is integrated, keeping the same
response shape: options, recommended, explanation {summary, factors, confidence, data_sources}.
"""

import datetime
import itertools
import math
import re
from typing import Any, Dict, List, Optional

IST = datetime.timedelta(hours=5, minutes=30)
CUTOFF_HOUR = 16  # orders after this leave the next day (matches the Delivery rules page)
HANDLING_HOURS = 4

CITIES = {
    "bengaluru": (12.97, 77.59), "hyderabad": (17.39, 78.49), "mumbai": (19.08, 72.88), "pune": (18.52, 73.86),
    "chennai": (13.08, 80.27), "delhi": (28.61, 77.21), "kolkata": (22.57, 88.36), "ahmedabad": (23.02, 72.57),
    "kochi": (9.93, 76.27), "jaipur": (26.91, 75.79), "mysuru": (12.30, 76.64), "coimbatore": (11.02, 76.96),
}

# name, max load kg, max volume l, average km/h, $ per km, $ fixed, g CO2 per km, max km on one trip (None: no limit)
VEHICLES = [
    {"name": "E-cargo bike", "max_kg": 40, "max_l": 150, "kmh": 18, "per_km": 0.05, "fixed": 1.0, "co2_g_km": 5, "max_km": 30},
    {"name": "Electric van", "max_kg": 800, "max_l": 4000, "kmh": 45, "per_km": 0.12, "fixed": 5.0, "co2_g_km": 20, "max_km": None},
    {"name": "Diesel van", "max_kg": 1000, "max_l": 5000, "kmh": 50, "per_km": 0.18, "fixed": 5.0, "co2_g_km": 210, "max_km": None},
    {"name": "Truck (12 t)", "max_kg": 12000, "max_l": 40000, "kmh": 45, "per_km": 0.45, "fixed": 20.0, "co2_g_km": 650, "max_km": None},
    {"name": "Rail freight + electric last mile", "max_kg": 20000, "max_l": 60000, "kmh": 35, "per_km": 0.08, "fixed": 40.0, "co2_g_km": 30, "max_km": None, "min_km": 400},
    {"name": "Air express (partner carrier)", "max_kg": 30, "max_l": 200, "kmh": 300, "per_km": 1.2, "fixed": 15.0, "co2_g_km": 600, "max_km": None, "min_km": 500, "extra_hours": 6},
]
EV_RANGE_KM = 250  # an electric van stops to charge every 250 km

# road choices: distance factor, speed factor, toll $, emissions factor
PATHS = [
    {"name": "Expressway", "dist": 1.08, "speed": 1.15, "toll": 4.0, "co2": 0.92},
    {"name": "National highway", "dist": 1.00, "speed": 1.00, "toll": 1.5, "co2": 1.00},
    {"name": "Toll-free state roads", "dist": 1.12, "speed": 0.85, "toll": 0.0, "co2": 1.10},
]
OBJECTIVE_METRIC = {"shortest": "distance_km", "fastest": "hours", "cheapest": "cost_usd", "greenest": "co2_kg"}
OBJECTIVE_WORD = {"shortest": "the shortest distance", "fastest": "the fastest arrival", "cheapest": "the lowest cost", "greenest": "the lowest emissions"}

DECISIONS: Dict[str, Dict[str, Any]] = {}
_ids = itertools.count(1)
SOURCES = ["Shipment origin and destination", "Road distance between cities", "Vehicle speed, cost and emissions profiles"]

def _a(word: str) -> str:
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word

def _now() -> datetime.datetime:
    return datetime.datetime.utcnow() + IST

def _city(place: str) -> Optional[str]:
    text = (place or "").lower()
    inside = re.findall(r"\(([^)]+)\)", text)
    for chunk in inside + [text]:
        for name in CITIES:
            if name in chunk:
                return name
    return None

def _km(a: str, b: str) -> float:
    (la1, lo1), (la2, lo2) = CITIES[a], CITIES[b]
    p1, p2 = math.radians(la1), math.radians(la2)
    d = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2
    straight = 6371 * 2 * math.asin(math.sqrt(d))
    return max(8.0, straight * 1.25)  # within one city: about 8 km

def _legs(shipment: Dict[str, Any], stops: Optional[List[str]]) -> Dict[str, Any]:
    names = [shipment.get("origin", "")] + list(stops or []) + [shipment.get("destination", "")]
    cities, assumed = [], []
    for n in names:
        c = _city(n)
        if c is None:
            c = "bengaluru"
            assumed.append(n or "an empty place")
        cities.append(c)
    km = sum(_km(a, b) for a, b in zip(cities, cities[1:]))
    return {"cities": [c.title() for c in cities], "km": km, "assumed": assumed}

def _trip(vehicle: Dict[str, Any], km: float, path: Dict[str, Any]) -> Dict[str, Any]:
    dist = km * path["dist"]
    hours = dist / (vehicle["kmh"] * path["speed"]) + vehicle.get("extra_hours", 0)
    if vehicle["name"] == "Electric van":
        hours += 0.75 * int(dist // EV_RANGE_KM)  # charging stops
    cost = vehicle["fixed"] + dist * vehicle["per_km"] + path["toll"]
    co2 = dist * vehicle["co2_g_km"] * path["co2"] / 1000
    return {"distance_km": round(dist, 1), "hours": round(hours, 1), "cost_usd": round(cost, 2), "co2_kg": round(co2, 2)}

def _fits(vehicle: Dict[str, Any], km: float, kg: float, litres: float) -> Optional[str]:
    """None if the vehicle can take the load; otherwise why not."""
    if kg > vehicle["max_kg"]:
        return f"too heavy ({kg:g} kg, takes up to {vehicle['max_kg']} kg)"
    if litres > vehicle["max_l"]:
        return f"too bulky ({litres:g} l, takes up to {vehicle['max_l']} l)"
    if vehicle.get("max_km") and km > vehicle["max_km"]:
        return f"too far ({km:.0f} km, range {vehicle['max_km']} km)"
    if vehicle.get("min_km") and km < vehicle["min_km"]:
        return f"only worth it above {vehicle['min_km']} km"
    return None

def _save(kind: str, shipment: Dict[str, Any], options: List[Dict[str, Any]], recommended: str, explanation: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    decision = {"decision_id": f"dec-{next(_ids)}", "kind": kind, "shipment_id": shipment["shipment_id"], "created_at": _now().strftime("%Y-%m-%d %H:%M IST"),
                "options": options, "recommended": recommended, "explanation": {**explanation, "data_sources": SOURCES, "model": "AuraCommerce delivery planner"},
                "status": "proposed", "preview": True, **extra}
    DECISIONS[decision["decision_id"]] = decision
    return decision

def _load(shipment: Dict[str, Any], kg: Optional[float], litres: Optional[float]) -> tuple:
    return (float(kg if kg not in (None, "") else shipment.get("weight_kg", 5)), float(litres if litres not in (None, "") else shipment.get("volume_l", 20)))

def _vehicle_for(shipment: Dict[str, Any], km: float) -> Dict[str, Any]:
    """The vehicle already chosen for the shipment, or the one the vehicle model would pick."""
    chosen = next((v for v in VEHICLES if v["name"] == shipment.get("vehicle")), None)
    if chosen:
        return chosen
    kg, litres = _load(shipment, None, None)
    return _rank_vehicles(km, kg, litres)[0][0]

def _rank_vehicles(km: float, kg: float, litres: float) -> List[tuple]:
    path = PATHS[1]
    fit = [(v, _trip(v, km, path)) for v in VEHICLES if _fits(v, km, kg, litres) is None]
    if not fit:
        return []
    top = {m: max(t[m] for _, t in fit) or 1 for m in ("co2_kg", "cost_usd", "hours")}
    score = lambda t: 0.4 * t["co2_kg"] / top["co2_kg"] + 0.35 * t["cost_usd"] / top["cost_usd"] + 0.25 * t["hours"] / top["hours"]
    return sorted(fit, key=lambda vt: score(vt[1]))

# ---- the four recommendations ----

def recommend_route(shipment: Dict[str, Any], objective: Optional[str], stops: Optional[List[str]]) -> Dict[str, Any]:
    objective = objective or "greenest"
    legs = _legs(shipment, stops)
    vehicle = _vehicle_for(shipment, legs["km"])
    options = [{"name": p["name"], "vehicle": vehicle["name"], "via": " → ".join(legs["cities"]), **_trip(vehicle, legs["km"], p)} for p in PATHS]
    metric = OBJECTIVE_METRIC[objective]
    best = min(options, key=lambda o: o[metric])
    others = [o for o in options if o is not best]
    factors = [f"Goal: {OBJECTIVE_WORD[objective]}. {best['name']} scores {best[metric]} on that, against "
               + ", ".join(f"{o['name']} {o[metric]}" for o in others) + "."]
    if objective != "fastest":
        fastest = min(options, key=lambda o: o["hours"])
        if fastest is not best:
            factors.append(f"It takes {round(best['hours'] - fastest['hours'], 1)} h longer than the {fastest['name']}.")
    if objective != "greenest":
        greenest = min(options, key=lambda o: o["co2_kg"])
        if greenest is not best:
            factors.append(f"It emits {round(best['co2_kg'] - greenest['co2_kg'], 2)} kg more CO2 than the {greenest['name']}.")
    factors.append(f"Planned for {_a(vehicle['name'].lower())}{' (the vehicle already chosen)' if shipment.get('vehicle') else ' (the recommended vehicle)'}.")
    if len(legs["cities"]) > 2:
        factors.append(f"Covers {len(legs['cities']) - 2} extra stop(s) in the order given.")
    if legs["assumed"]:
        factors.append("Location not recognised, assumed Bengaluru: " + ", ".join(legs["assumed"]) + ".")
    summary = f"Take the {best['name']} ({best['distance_km']} km, about {best['hours']} h, ${best['cost_usd']}, {best['co2_kg']} kg CO2): it gives {OBJECTIVE_WORD[objective]}."
    return _save("route", shipment, options, best["name"], {"summary": summary, "factors": factors, "confidence": 0.7 if legs["assumed"] else 0.85}, {"objective": objective})

def recommend_vehicle(shipment: Dict[str, Any], kg: Optional[float], litres: Optional[float]) -> Dict[str, Any]:
    kg, litres = _load(shipment, kg, litres)
    legs = _legs(shipment, None)
    km = legs["km"]
    ranked = _rank_vehicles(km, kg, litres)
    options = []
    for v in VEHICLES:
        why_not = _fits(v, km, kg, litres)
        trip = _trip(v, km, PATHS[1])
        options.append({"name": v["name"], "fits": why_not is None, "why_not": why_not, **trip})
    if not ranked:
        raise ValueError(f"No vehicle type can take {kg:g} kg / {litres:g} l over {km:.0f} km. Split the shipment.")
    best, trip = ranked[0]
    factors = [f"Load {kg:g} kg and {litres:g} l over about {km:.0f} km ({' → '.join(legs['cities'])}).",
               f"{best['name']}: {trip['co2_kg']} kg CO2, ${trip['cost_usd']}, about {trip['hours']} h.",
               "Ranked on emissions (40%), cost (35%) and time (25%) among the vehicles that fit."]
    if len(ranked) > 1:
        nv, nt = ranked[1]
        factors.append(f"Next best: {nv['name']} ({nt['co2_kg']} kg CO2, ${nt['cost_usd']}, {nt['hours']} h).")
    ruled_out = [f"{o['name']}: {o['why_not']}" for o in options if not o["fits"]]
    if ruled_out:
        factors.append("Ruled out: " + "; ".join(ruled_out) + ".")
    summary = f"Use {_a(best['name'].lower())}: it fits the load and gives the best balance of emissions, cost and time for this distance."
    return _save("vehicle", shipment, options, best["name"], {"summary": summary, "factors": factors, "confidence": 0.8}, {"weight_kg": kg, "volume_l": litres})

def _depart(now: datetime.datetime) -> tuple:
    """When the shipment can leave, and why."""
    reasons = []
    leave = now + datetime.timedelta(hours=HANDLING_HOURS)
    if now.hour >= CUTOFF_HOUR:
        leave = (now + datetime.timedelta(days=1)).replace(hour=9, minute=0)
        reasons.append(f"Booked after the {CUTOFF_HOUR}:00 cut-off, so it leaves tomorrow at 09:00.")
    else:
        reasons.append(f"Packing and handover take about {HANDLING_HOURS} h.")
    if leave.weekday() == 6:
        leave = (leave + datetime.timedelta(days=1)).replace(hour=9, minute=0)
        reasons.append("No dispatch on Sunday, so it leaves Monday.")
    return leave, reasons

def predict_eta(shipment: Dict[str, Any]) -> Dict[str, Any]:
    legs = _legs(shipment, None)
    vehicle = _vehicle_for(shipment, legs["km"])
    path = next((p for p in PATHS if p["name"] == shipment.get("route")), PATHS[1])
    trip = _trip(vehicle, legs["km"], path)
    leave, factors = _depart(_now())
    hours = trip["hours"]
    if vehicle["kmh"] < 100 and hours > 10:
        rest = 8 * int(hours // 10)
        hours += rest
        factors.append(f"Driver rest of {rest} h on a long road trip.")
    arrive = leave + datetime.timedelta(hours=hours)
    if arrive.weekday() == 0 or leave.weekday() == 0:
        arrive += datetime.timedelta(hours=3)
        factors.append("Monday delays: weekend orders leave the warehouse late (from Delivery insights).")
    if arrive.hour >= 21 or arrive.hour < 9:
        nxt = arrive if arrive.hour < 9 else arrive + datetime.timedelta(days=1)
        arrive = nxt.replace(hour=10, minute=0)
        factors.append("Arrives outside delivery hours (09:00 to 21:00), so it is delivered the next morning.")
    spread = datetime.timedelta(hours=round(1 + 0.1 * hours, 1))
    factors.insert(0, f"{vehicle['name']} on the {path['name']}: {trip['distance_km']} km, about {trip['hours']} h on the road.")
    if legs["assumed"]:
        factors.append("Location not recognised, assumed Bengaluru: " + ", ".join(legs["assumed"]) + ".")
    confidence = round(max(0.55, 0.9 - legs["km"] / 5000 - (0.1 if legs["assumed"] else 0)), 2)
    fmt = lambda d: d.strftime("%a %d %b, %H:%M")
    options = [{"name": "Predicted", "eta": fmt(arrive), "earliest": fmt(arrive - spread), "latest": fmt(arrive + spread)}]
    summary = f"Expected {fmt(arrive)} IST, between {fmt(arrive - spread)} and {fmt(arrive + spread)}."
    return _save("eta", shipment, options, "Predicted", {"summary": summary, "factors": factors, "confidence": confidence}, {"eta_iso": arrive.isoformat(timespec="minutes")})

SLOTS = [(9, 12), (12, 15), (15, 18), (18, 21)]

def recommend_slots(shipment: Dict[str, Any], start: Optional[str]) -> Dict[str, Any]:
    eta = predict_eta(shipment)
    DECISIONS.pop(eta["decision_id"], None)  # only used as an input here
    arrive = datetime.datetime.fromisoformat(eta["eta_iso"])
    first = datetime.datetime.fromisoformat(start) if start else arrive.replace(hour=0, minute=0)
    options = []
    for day in range(3):
        d = (first + datetime.timedelta(days=day)).replace(minute=0)
        if d.weekday() == 6:
            continue
        for a, b in SLOTS:
            begin, end = d.replace(hour=a), d.replace(hour=b)
            if end <= arrive:
                continue  # it cannot be there yet
            p = 0.95 - (0.25 if begin < arrive else 0) - (0.06 if d.weekday() == 0 else 0) - (0.03 if a == 18 else 0) - 0.02 * day
            options.append({"name": f"{begin.strftime('%a %d %b')} {a:02d}:00-{b:02d}:00", "on_time_chance": round(max(0.3, min(0.97, p)), 2),
                            "note": "Starts before the predicted arrival" if begin < arrive else ("Monday" if d.weekday() == 0 else "")})
    options.sort(key=lambda o: -o["on_time_chance"])
    options = options[:6]
    best = options[0]
    factors = [f"Predicted arrival {eta['options'][0]['eta']} IST; slots that end before it are left out.",
               "Slots that start before the predicted arrival are less likely to be met.",
               "Monday slots and the evening slot are a little riskier (delivery insights); later days lose a little for waiting time.",
               f"Best: {best['name']}, about {int(best['on_time_chance'] * 100)}% likely to be on time."]
    summary = f"Offer {best['name']} first; it is the most likely to be met."
    return _save("slot", shipment, options, best["name"], {"summary": summary, "factors": factors, "confidence": eta["explanation"]["confidence"]}, {})

# ---- reading, accepting and overriding ----

def get_decision(decision_id: str) -> Dict[str, Any]:
    if decision_id not in DECISIONS:
        raise LookupError(f"No recommendation {decision_id}")
    return DECISIONS[decision_id]

def apply(decision_id: str, shipment: Dict[str, Any], choice: Optional[str], reason: Optional[str], actor: Optional[str]) -> Dict[str, Any]:
    d = get_decision(decision_id)
    if d["status"] != "proposed":
        raise ValueError(f"This recommendation was already {d['status']}")
    names = [o["name"] for o in d["options"]]
    pick = choice or d["recommended"]
    if pick not in names:
        raise ValueError("Choose one of: " + ", ".join(names))
    option = next(o for o in d["options"] if o["name"] == pick)
    if d["kind"] == "vehicle" and not option.get("fits", True):
        raise ValueError(f"{pick} cannot take this shipment: {option['why_not']}")
    overridden = pick != d["recommended"]
    if overridden and not (reason or "").strip():
        raise ValueError("Say why you are overriding the recommendation")
    if d["kind"] == "route":
        shipment["route"] = pick
    elif d["kind"] == "vehicle":
        shipment["vehicle"] = pick
    elif d["kind"] == "eta":
        shipment["eta"] = option["eta"]
    elif d["kind"] == "slot":
        shipment["delivery_slot"] = pick
    d.update({"status": "overridden" if overridden else "accepted", "chosen": pick, "reason": reason or "", "decided_by": actor or "", "decided_at": _now().strftime("%Y-%m-%d %H:%M IST")})
    shipment.setdefault("decisions", []).insert(0, {k: d[k] for k in ("decision_id", "kind", "recommended", "chosen", "status", "reason", "decided_by", "decided_at")})
    return {"decision": d, "shipment": shipment}
