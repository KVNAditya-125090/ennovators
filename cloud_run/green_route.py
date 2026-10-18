"""
Cloud Run - green route recommendations
For a load going from one place to another, recommends the vehicle with the lowest emissions that can carry it that far, says what it
would save against a conventional delivery, and lets staff select it and record the saving against a real shipment.

  route/green/recommend   origin and destination (a city or address, or lat and lng) and the weight: every vehicle that can take
                          the load is worked out, the lowest-emission one is recommended and compared with a diesel van (or a
                          truck when the load is too heavy for one)
  route/green/select      staff choose the recommendation
  route/green/explain     the reasons, in plain words
  route/green/impact      the saving of a selected recommendation is recorded against a shipment, once, and joins the impact ledger

The distances and emissions come from the delivery planner's own tables (straight-line distance between places times a road
factor, typical vehicle figures), so they are estimates, not live traffic or measured emissions.
"""

import datetime
from typing import Any, Callable, Dict, List

from firestore import store
from firestore.users.consumer import operations as ops
from firestore.services.taas import firestore_taas
from vertex_ai.services.taas import planner
from cloud_run.ids import new_id
from cloud_run import impact

PATH = planner.PATHS[1]   # the national highway: the planner's neutral road choice
CONVENTIONAL = ("Diesel van", "Truck (12 t)")


def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _place(value: Any, what: str):
    obj = value if isinstance(value, dict) else {"address": str(value)}
    if "lat" in obj and "lng" in obj:
        try:
            lat, lng = float(obj["lat"]), float(obj["lng"])
        except (TypeError, ValueError):
            raise ValueError(f"The {what} needs a number for lat and lng.")
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError(f"The {what} lat and lng are out of range.")
        return str(obj.get("name") or f"{lat:.3f}, {lng:.3f}"), (lat, lng)
    text = str(obj.get("city") or obj.get("address") or obj.get("name") or "").strip()
    found = planner._point(text) if text else None
    if found is None:
        raise ValueError(f"Could not find the {what} '{text}'. Give a town or city, or its lat and lng.")
    return found


def _log(tenant_id: str) -> List[Dict[str, Any]]:
    return store.kdoc("green_routes", "all", lambda: {"items": []}, tenant_id=tenant_id)["items"]


def _rec(tenant, recommendation_id: str) -> Dict[str, Any]:
    rec = next((r for r in _log(tenant["tenant_id"]) if r["recommendation_id"] == recommendation_id), None)
    if rec is None:
        raise LookupError(f"No green route recommendation {recommendation_id}")
    return rec


def recommend(tenant, params):
    (o_name, o_pt), (d_name, d_pt) = _place(params["origin"], "origin"), _place(params["destination"], "destination")
    kg = float(params.get("weight_kg") or 5)
    if not 0 < kg <= 30000:
        raise ValueError("The weight must be above 0 and at most 30,000 kg.")
    km = planner._km(o_pt, d_pt)
    options = []
    for v in planner.VEHICLES:
        if planner._fits(v, km, kg, 0.0) is None:
            options.append({"vehicle": v["name"], **planner._trip(v, km, PATH)})
    if not options:
        raise ValueError(f"No vehicle can take {kg:g} kg over about {km:.0f} km.")
    options.sort(key=lambda o: (o["co2_kg"], o["cost_usd"]))
    best = options[0]
    base = next((o for name in CONVENTIONAL for o in options if o["vehicle"] == name), None)
    saved = round(max(0.0, base["co2_kg"] - best["co2_kg"]), 2) if base else 0.0
    factors = [f"{best['vehicle']} gives the lowest emissions of the {len(options)} vehicle(s) that can carry {kg:g} kg over about {best['distance_km']} km: {best['co2_kg']} kg CO2."]
    if base and base is not best:
        factors.append(f"A {base['vehicle'].lower()} would emit {base['co2_kg']} kg CO2 for the same trip, so this saves {saved} kg.")
    faster = min(options, key=lambda o: o["hours"])
    if faster is not best:
        factors.append(f"It takes {round(best['hours'] - faster['hours'], 1)} h longer than the {faster['vehicle'].lower()}, the fastest choice.")
    cheaper = min(options, key=lambda o: o["cost_usd"])
    if cheaper is not best:
        factors.append(f"It costs ${round(best['cost_usd'] - cheaper['cost_usd'], 2)} more than the {cheaper['vehicle'].lower()}, the cheapest choice.")
    rec = {"recommendation_id": new_id(), "origin": o_name, "destination": d_name, "weight_kg": kg, "distance_km": best["distance_km"],
           "recommended": best, "baseline": base, "co2_saved_kg": saved, "alternatives": options[1:],
           "explanation": {"summary": f"Send it by {best['vehicle'].lower()}: {best['co2_kg']} kg CO2 over {best['distance_km']} km" + (f", {saved} kg less than {base['vehicle'].lower()}." if base and saved else "."),
                           "factors": factors, "confidence": 0.8, "data_sources": ["Distance between the two places (straight line times a road factor)", "Typical vehicle emissions, cost and speed"]},
           "status": "recommended", "at": _now(), "by": ops.ACTOR.get() or "AI"}
    items = _log(tenant["tenant_id"])
    items.insert(0, rec)
    del items[100:]
    return rec


def select(tenant, params):
    rec = _rec(tenant, params["recommendation_id"])
    if rec["status"] != "recommended":
        raise ValueError(f"This recommendation is already {rec['status']}.")
    rec.update({"status": "selected", "selected_at": _now(), "selected_by": ops.ACTOR.get() or ""})
    return rec


def explain(tenant, params):
    rec = _rec(tenant, params["recommendation_id"])
    return {"recommendation_id": rec["recommendation_id"], "status": rec["status"], **rec["explanation"]}


def impact_record(tenant, params):
    rec = _rec(tenant, params["route_id"])
    if rec["status"] != "selected":
        raise ValueError("Select the recommendation first: only a chosen green route has a saving to record.")
    if rec.get("impact"):
        raise ValueError("The saving of this route was already recorded.")
    shipment = ops._find(firestore_taas.list_shipments(), "shipment_id", params["shipment_id"])
    saved = rec["co2_saved_kg"]
    shipment["green_route"] = {"recommendation_id": rec["recommendation_id"], "vehicle": rec["recommended"]["vehicle"], "co2_saved_kg": saved}
    rec["impact"] = {"shipment_id": shipment["shipment_id"], "co2_saved_kg": saved, "at": _now()}
    impact.add_record(tenant["tenant_id"], "taas", "event", f"green route {rec['recommendation_id'][:8]} for {shipment['shipment_id']}", saved, "kg CO2e", {"shipment_id": shipment["shipment_id"]})
    return {"status": "recorded", "shipment_id": shipment["shipment_id"], "vehicle": rec["recommended"]["vehicle"], "co2_saved_kg": saved}


def install(handlers: Dict[str, Callable]) -> int:
    table = {"/taas/route/green/recommend/v1": recommend, "/taas/route/green/select/v1": select,
             "/taas/route/green/explain/v1": explain, "/taas/route/green/impact/v1": impact_record}
    handlers.update(table)
    return len(table)
