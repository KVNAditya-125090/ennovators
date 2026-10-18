"""
Cloud Run - impact reports, records and the notes behind each figure
The sustainability side of the consumer's dashboard, kept as reports that can be exported:

  records          baseline/record and event/record keep what would have happened without the platform (an unsold item, a
                   default diesel route, a discarded item) and the saving from each event. Recorded savings in kg CO2e also
                   join the impact ledger.
  report/generate  a stored snapshot of one service's impact figures (Product, Transport or Support), with a figure id for each
  net/generate     the platform-wide net figures, or one service's
  report/export    a stored report as CSV (for ESG reporting). PDF is not built yet and is refused plainly.
  source-confidence / baseline/method   for a figure id: where the number comes from, how far to trust it, and what it is
                   compared against

The figures themselves are worked out from the consumer's own records by cloud_run/insights.py. They count everything recorded so
far: a period is a label on the report, not a filter. They are estimates against a stated baseline, not measurements.
"""

import csv
import datetime
import io
import math
from typing import Any, Callable, Dict, List

from firestore import store
from firestore.users.consumer import operations as ops
from cloud_run.ids import new_id
from cloud_run import insights

FIGURES: Dict[str, Dict[str, str]] = {
    "paas.items_resold": {"label": "Items resold", "unit": "items", "source": "Orders that are paid, shipped or delivered, counted by item.",
                          "confidence": "High: counted from the consumer's own orders.", "baseline": "Not compared with anything: it is a count."},
    "paas.co2_saved_kg": {"label": "Carbon saved by resale", "unit": "kg CO2e", "source": "The carbon footprint recorded on each product, times the units sold.",
                          "confidence": "Medium: the per-product figures are entered by the seller, not measured.", "baseline": "Buying each item new instead of refurbished."},
    "taas.co2_saved_kg": {"label": "Carbon saved by delivery", "unit": "kg CO2e", "source": "The saving recorded on each shipment that was not cancelled.",
                          "confidence": "Medium: estimated by the delivery planner from typical vehicle emissions, not measured on the road.",
                          "baseline": f"A conventional diesel delivery ({insights.BASELINE_KG_PER_DELIVERY} kg CO2e, an assumption)."},
    "taas.deliveries": {"label": "Deliveries", "unit": "deliveries", "source": "Shipments that were not cancelled.", "confidence": "High: counted.", "baseline": "Not compared with anything: it is a count."},
    "taas.electric_share_pct": {"label": "Electric share of deliveries", "unit": "%", "source": "Shipments flagged as electric.", "confidence": "High: counted.", "baseline": "Not compared with anything."},
    "taas.returns_recovered": {"label": "Returns recovered", "unit": "returns", "source": "Returns given a route (resale, refurbish and so on).", "confidence": "High: counted.", "baseline": "Not compared with anything."},
    "saas.items_kept_out_of_landfill": {"label": "Items kept out of landfill", "unit": "items", "source": "Returns given a route.", "confidence": "High: counted.", "baseline": "Every returned item discarded."},
    "saas.co2_saved_kg": {"label": "Carbon saved by recovery", "unit": "kg CO2e", "source": "Returns routed to resale or refurbish, times the product's recorded carbon footprint.",
                          "confidence": "Medium-low: assumes each recovered item stands in for one new item.", "baseline": "The item discarded and replaced with a new one."},
    "maas.net_co2_saved_kg": {"label": "Net carbon saved", "unit": "kg CO2e", "source": "The impact ledger: resale, delivery and recovery events, plus recorded savings.",
                              "confidence": "Medium: the sum of the estimates above.", "baseline": "Everything bought new, delivered by diesel and returns discarded."},
    "maas.delivery_co2_actual_kg": {"label": "Delivery emissions (actual plan)", "unit": "kg CO2e", "source": "The emissions planned for each shipment.", "confidence": "Medium: estimated, not measured.", "baseline": "See the baseline delivery figure."},
    "maas.delivery_co2_baseline_kg": {"label": "Delivery emissions (baseline)", "unit": "kg CO2e", "source": "Shipments times the diesel delivery assumption.", "confidence": "Low: rests on one assumed figure.", "baseline": "A conventional diesel delivery for every shipment."},
    "maas.ai_energy_wh": {"label": "Energy used by the AI", "unit": "Wh", "source": "AI calls in the last 30 days times an assumed energy per request.", "confidence": f"Low: assumes {insights.AI_WH_PER_REQUEST} Wh per request.", "baseline": "Not compared with anything."},
}
SERVICE_FIGURES = {"paas": ("paas", insights.paas_impact, ["items_resold", "co2_saved_kg"]),
                   "taas": ("taas", insights.transport_impact, ["co2_saved_kg", "deliveries", "electric_share_pct", "returns_recovered"]),
                   "saas": ("saas", insights.support_impact, ["items_kept_out_of_landfill", "co2_saved_kg"])}
UNITS_OF_SAVING_KG = ("kg CO2e", "kg co2e", "kg")


def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _number(value: Any, what: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{what} must be a number.")
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{what} cannot be negative.")
    return number


# ---------- records ----------
def records(tenant_id: str) -> List[Dict[str, Any]]:
    return store.kdoc("impact_records", "all", lambda: {"items": []}, tenant_id=tenant_id)["items"]


def add_record(tenant_id: str, service: str, kind: str, subject: str, value: float, unit: str, detail: Dict[str, Any] = None) -> Dict[str, Any]:
    items = records(tenant_id)
    record = {"record_id": new_id(), "service": service, "kind": kind, "subject": str(subject)[:120], "value": round(float(value), 3),
              "unit": str(unit).strip()[:20] or "units", "detail": detail or {}, "at": _now(), "by": ops.ACTOR.get() or "System"}
    items.insert(0, record)
    del items[500:]
    return record


def _recorder(service: str, kind: str, subject_key: str, value_key: str, unit_key: str = None, fixed_unit: str = None, extra: tuple = ()):
    def handler(tenant, params):
        value = _number(params[value_key], value_key.replace("_", " ").capitalize())
        unit = fixed_unit or str(params[unit_key]).strip()
        if not unit:
            raise ValueError("Give the unit.")
        record = add_record(tenant["tenant_id"], service, kind, params[subject_key], value, unit, {k: params.get(k) for k in extra})
        return {"status": "recorded", "record": record}
    return handler


# ---------- reports ----------
def _reports(tenant_id: str) -> List[Dict[str, Any]]:
    return store.kdoc("impact_reports", "all", lambda: {"items": []}, tenant_id=tenant_id)["items"]


def _period(value: Any) -> str:
    period = str(value or "").strip()
    if not period or len(period) > 40:
        raise ValueError("Name the period, for example 2026-10 or 'last 30 days'.")
    return period


def _recorded_summary(tenant_id: str, service: str) -> Dict[str, Any]:
    mine = [r for r in records(tenant_id) if r["service"] == service]
    by_unit: Dict[str, float] = {}
    for r in mine:
        if r["kind"] == "event":
            by_unit[r["unit"]] = round(by_unit.get(r["unit"], 0) + r["value"], 3)
    return {"baselines_recorded": sum(1 for r in mine if r["kind"] == "baseline"), "events_recorded": sum(1 for r in mine if r["kind"] == "event"), "recorded_savings_by_unit": by_unit}


def _store(tenant, service: str, period: str, figures: List[Dict[str, Any]], extra: Dict[str, Any]) -> Dict[str, Any]:
    report = {"report_id": new_id(), "service": service, "period": period, "figures": figures, **extra, "generated_at": _now(), "generated_by": ops.ACTOR.get() or "System",
              "note": "Figures cover every record to date: the period is a label. They are estimates against the baseline method, not measurements."}
    items = _reports(tenant["tenant_id"])
    items.insert(0, report)
    del items[100:]
    return report


def _figure(fid: str, value: Any) -> Dict[str, Any]:
    meta = FIGURES[fid]
    return {"figure_id": fid, "label": meta["label"], "value": value, "unit": meta["unit"]}


def _generate(service: str):
    prefix, compute, keys = SERVICE_FIGURES[service]
    def handler(tenant, params):
        period = _period(params["period"])
        result = compute(tenant, {})
        figures = [_figure(f"{prefix}.{k}", result.get(k)) for k in keys]
        return _store(tenant, service.upper(), period, figures, {"basis": result.get("basis"), "recorded": _recorded_summary(tenant["tenant_id"], service)})
    return handler


def net_generate(tenant, params):
    period = _period(params["period"])
    service = params.get("service")
    ledger = insights.impact_ledger(tenant, {})
    net = insights.net_impact(tenant, {})
    if service in (None, "", "maas"):
        figures = [_figure("maas.net_co2_saved_kg", ledger["total_co2_saved_kg"]), _figure("maas.delivery_co2_actual_kg", net["delivery_co2_actual_kg"]),
                   _figure("maas.delivery_co2_baseline_kg", net["delivery_co2_baseline_kg"]), _figure("maas.ai_energy_wh", insights.ai_footprint(tenant, {})["energy_wh"])]
        return _store(tenant, "MaaS", period, figures, {"by_service_co2_saved_kg": ledger["by_service"]})
    label = {"paas": "PaaS", "taas": "TaaS", "saas": "SaaS"}[service]
    return _store(tenant, label, period, [_figure(f"{service}.co2_saved_kg", ledger["by_service"].get(label, 0))], {"by_service_co2_saved_kg": {label: ledger["by_service"].get(label, 0)}})


def report_export(tenant, params):
    report = next((r for r in _reports(tenant["tenant_id"]) if r["report_id"] == params["report_id"]), None)
    if report is None:
        raise LookupError(f"No impact report {params['report_id']}")
    if params["format"] != "csv":
        raise ValueError("PDF export is not available yet. Export as csv.")
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["report_id", "service", "period", "generated_at", "figure_id", "label", "value", "unit", "source", "confidence", "baseline"])
    for f in report["figures"]:
        meta = FIGURES[f["figure_id"]]
        writer.writerow([report["report_id"], report["service"], report["period"], report["generated_at"], f["figure_id"], f["label"], f["value"], f["unit"], meta["source"], meta["confidence"], meta["baseline"]])
    return {"report_id": report["report_id"], "filename": f"impact-{report['service'].lower()}-{report['report_id'][:8]}.csv", "content_type": "text/csv", "content": out.getvalue()}


def _meta(figure_id: str) -> Dict[str, Any]:
    fid = str(figure_id).split(":")[-1]   # a figure id may be written report_id:figure_id
    if fid not in FIGURES:
        raise LookupError(f"No figure {figure_id}. Figure ids: " + ", ".join(FIGURES))
    return {"figure_id": fid, **FIGURES[fid]}


def source_confidence(tenant, params):
    m = _meta(params["figure_id"])
    return {"figure_id": m["figure_id"], "label": m["label"], "source": m["source"], "confidence": m["confidence"]}


def baseline_method(tenant, params):
    m = _meta(params["figure_id"])
    return {"figure_id": m["figure_id"], "label": m["label"], "compared_with": m["baseline"], "method": insights.impact_baseline(tenant, {})["method"]}


def install(handlers: Dict[str, Callable]) -> int:
    table = {
        "/paas/impact/report/generate/v1": _generate("paas"), "/taas/impact/report/generate/v1": _generate("taas"), "/saas/impact/report/generate/v1": _generate("saas"),
        "/maas/impact/report/net/generate/v1": net_generate, "/maas/impact/report/export/v1": report_export,
        "/maas/impact/source-confidence/read/v1": source_confidence, "/maas/impact/baseline/method/read/v1": baseline_method,
        "/paas/impact/baseline/record/v1": _recorder("paas", "baseline", "event_type", "baseline_value", unit_key="unit"),
        "/paas/impact/event/record/v1": _recorder("paas", "event", "event_id", "saving", unit_key="unit"),
        "/taas/impact/baseline/record/v1": _recorder("taas", "baseline", "route_id", "baseline_value", fixed_unit="kg CO2e", extra=("default_mode",)),
        "/saas/impact/baseline/record/v1": _recorder("saas", "baseline", "item_id", "landfill_kg", fixed_unit="kg"),
        "/saas/impact/event/record/v1": _recorder("saas", "event", "event_id", "saving", unit_key="unit"),
    }
    handlers.update(table)
    return len(table)
