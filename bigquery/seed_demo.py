"""
BigQuery - demo figures.
Makes up the history the Owner and consumer dashboards need so their charts have something to draw:

  BigQuery  sales_daily          units sold per day for each product, 120 days (feeds the demand forecast)
  BigQuery  hosting_cost_daily   hosting cost per day and component, 90 days (feeds the budget)
  Cloud SQL audit_log            about four months of calls to the API, every line marked demo = true

All of it is invented, and the calls are marked so they can be taken out again. A billing export and the real traffic
replace these once the platform is in use.

    python -m bigquery.seed_demo            add or refresh
    python -m bigquery.seed_demo --remove   take out the demo calls and empty the two tables
"""

import datetime
import hashlib
import json
import sys
from typing import Dict, List

from bigquery.services.maas import DATASET, HOSTING_PLAN, PROJECT, client
from cloud_sql import db
from cloud_sql.services.maas import cloud_sql_maas as maas
from cloud_sql.services.maas.endpoints import endpoint_registry as registry

CONSUMER = "Lakshmi Demo Retail"

def unit(*parts: str) -> float:
    """A repeatable pseudo-random number between 0 and 1, so the same inputs always give the same figure."""
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF

def ensure_tables() -> None:
    from google.cloud import bigquery
    bq = client()
    bq.create_dataset(bigquery.Dataset(f"{PROJECT}.{DATASET}"), exists_ok=True)
    for name, schema in (("sales_daily", [("day", "DATE"), ("sku", "STRING"), ("units", "INT64")]),
                         ("hosting_cost_daily", [("day", "DATE"), ("component", "STRING"), ("usd", "FLOAT64")])):
        bq.create_table(bigquery.Table(f"{PROJECT}.{DATASET}.{name}", schema=[bigquery.SchemaField(n, t) for n, t in schema]), exists_ok=True)

def load(table: str, rows: List[Dict[str, object]]) -> None:
    from google.cloud import bigquery
    config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON)
    client().load_table_from_json(rows, f"{PROJECT}.{DATASET}.{table}", job_config=config).result()

# a product's usual daily sales: its sku and a base number of units
SALES = [("SKU-PHN-A1", 3.0), ("SKU-LAP-14", 1.6), ("SKU-TAB-10", 2.0), ("SKU-WCH-S3", 2.4), ("SKU-AUD-NC", 2.2), ("SKU-AUD-EB", 4.2),
         ("SKU-SPK-BT", 2.6), ("SKU-PWR-SL", 4.8), ("SKU-LMP-SL", 5.4), ("SKU-KTL-E1", 3.4), ("SKU-MXR-G3", 2.2), ("SKU-APF-HP", 1.1)]
WEEKDAY = [0.85, 0.9, 0.95, 1.0, 1.15, 1.45, 1.25]  # Monday to Sunday: weekends sell more

def sales_rows() -> List[Dict[str, object]]:
    today = datetime.date.today()
    rows = []
    for sku, base in SALES:
        for ago in range(120, 0, -1):
            day = today - datetime.timedelta(days=ago)
            growth = 0.8 + 0.4 * (1 - ago / 120)  # sales grow gently over the period
            noise = 0.75 + 0.5 * unit(sku, day.isoformat())
            rows.append({"day": day.isoformat(), "sku": sku, "units": max(0, round(base * WEEKDAY[day.weekday()] * growth * noise))})
    return rows

def cost_rows() -> List[Dict[str, object]]:
    today = datetime.date.today()
    rows = []
    for component, planned in HOSTING_PLAN:
        for ago in range(90, 0, -1):
            day = today - datetime.timedelta(days=ago)
            rows.append({"day": day.isoformat(), "component": component, "usd": round(planned / 90 * (0.28 + 0.24 * unit(component, day.isoformat())) , 4)})
    return rows

# the calls a consumer's team and shoppers make: path, method, weight
CALLS = [("/paas/catalog/product/read/v1", "GET", 14), ("/paas/order/read/staff/v1", "GET", 8), ("/paas/inventory/stock/read/v1", "GET", 6),
         ("/taas/shipment/read/staff/v1", "GET", 7), ("/saas/ticket/read/staff/v1", "GET", 6), ("/maas/analytics/dashboard/read/v1", "GET", 3),
         ("/paas/catalog/search/text/v1", "POST", 10), ("/paas/order/cart/add/v1", "POST", 6), ("/paas/order/checkout/place/v1", "POST", 2),
         ("/taas/tracking/read/v1", "GET", 5), ("/paas/assistant/chat/text-to-text/v1", "POST", 7), ("/paas/wishlist/read/v1", "GET", 3),
         ("/saas/ticket/create/query/v1", "POST", 1), ("/paas/forecast/demand/read/v1", "GET", 3), ("/saas/return/request/read/v1", "GET", 2),
         ("/taas/route/optimize/recommend/v1", "POST", 2), ("/paas/recommendation/product/read/v1", "GET", 4)]

def audit_rows(tenant_id: str, enabled: set) -> Dict[str, list]:
    calls = [c for c in CALLS if c[0] in enabled]
    total = sum(c[2] for c in calls)
    now = datetime.datetime.utcnow()
    out: Dict[str, list] = {"at": [], "path": [], "method": [], "status": [], "code": [], "ms": []}
    for ago in range(120, -1, -1):
        day = (now - datetime.timedelta(days=ago)).date()
        count = round((26 + 38 * unit("day", day.isoformat())) * WEEKDAY[day.weekday()] * (0.7 + 0.5 * (1 - ago / 120)))
        for i in range(count):
            r = unit("call", day.isoformat(), str(i))
            pick, acc = calls[-1], 0.0
            for c in calls:
                acc += c[2] / total
                if r * 0.999 <= acc:
                    pick = c
                    break
            roll = unit("status", day.isoformat(), str(i))
            if ago > 10 and roll > 0.993:
                status, code = 500, "server_error"       # a few server errors, all older than ten days
            elif roll > 0.985:
                status, code = 429, "rate_limited"
            elif roll > 0.968:
                status, code = 422, "invalid_request"
            else:
                status, code = 200, "ok"
            when = datetime.datetime.combine(day, datetime.time(7, 0)) + datetime.timedelta(seconds=int(unit("t", day.isoformat(), str(i)) * 14 * 3600))
            if ago == 0 and when > now:
                continue
            out["at"].append(when.strftime("%Y-%m-%d %H:%M:%S+00")); out["path"].append(pick[0]); out["method"].append(pick[1])
            out["status"].append(status); out["code"].append(code)
            out["ms"].append(round(35 + 520 * unit("ms", day.isoformat(), str(i)) ** 2, 1))
    return out

def main(remove: bool = False) -> int:
    from cloud_sql.schema import ensure_schema
    ensure_schema()  # the audit log needs its demo column
    tenant = maas.get_tenant_by_name(CONSUMER)
    if tenant is None:
        print(f"The consumer {CONSUMER} does not exist. Run: python -m cloud_sql.seed_demo")
        return 1
    db.run("DELETE FROM audit_log WHERE demo")
    if remove:
        ensure_tables(); load("sales_daily", []); load("hosting_cost_daily", [])
        print("Removed the demo calls and emptied sales_daily and hosting_cost_daily.")
        return 0
    ensure_tables()
    load("sales_daily", sales_rows())
    load("hosting_cost_daily", cost_rows())
    rows = audit_rows(tenant["tenant_id"], registry.enabled_paths(tenant["tenant_id"]))
    with db.tx() as conn:
        from sqlalchemy import text
        conn.execute(text("""INSERT INTO audit_log (at, tenant_id, path, method, status, code, ms, demo)
                             SELECT a, CAST(:t AS uuid), p, m, s, c, r, true
                             FROM unnest(CAST(CAST(:at AS text[]) AS timestamptz[]), CAST(:path AS text[]), CAST(:method AS text[]),
                                         CAST(:status AS integer[]), CAST(:code AS text[]), CAST(:ms AS real[])) AS x(a, p, m, s, c, r)"""),
                     {"t": tenant["tenant_id"], **rows})
    print(f"Loaded sales_daily ({len(sales_rows())} rows), hosting_cost_daily ({len(cost_rows())} rows) and {len(rows['at'])} demo calls into the audit log.")
    return 0

if __name__ == "__main__":
    sys.exit(main("--remove" in sys.argv))
