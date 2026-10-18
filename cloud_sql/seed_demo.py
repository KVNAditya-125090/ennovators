"""
Cloud SQL - demo accounts.
Creates the mock accounts for the demo (safe to run again: anything that exists is left alone). Every email and password
here is made up and is shown on the sign-in screen, so never reuse a real password. The app sends no mail.

    Owner     manager.owner@aionos.ai   developer.owner@aionos.ai   operator.owner@aionos.ai   (all see everything)
    Consumer  it.consumer@lakshmi.com (the Root, MaaS)  marketing.consumer@lakshmi.com (PaaS)
              operation.consumer@lakshmi.com (TaaS)     support.consumer@lakshmi.com (SaaS)
    Customer  individual.customer@gmail.com

    python -m cloud_sql.seed_demo
"""

import sys
from typing import Any, Dict, List

from cloud_sql import db
from cloud_sql.schema import ensure_schema
from cloud_sql.services.maas import cloud_sql_maas as maas
from cloud_sql.services.maas.endpoints import endpoint_registry as registry, SERVICE_ORDER
from cloud_sql.services.maas.roles import roles as role_store

CONSUMER = "Lakshmi Demo Retail"
CONSUMER_TYPE = "Circular retailer"

OWNERS = [
    ("Owner Manager", "manager.owner@aionos.ai", "Owner / Manager", "Manager@Demo2026"),
    ("Owner Developer", "developer.owner@aionos.ai", "Owner / Developer", "Developer@Demo2026"),
    ("Owner Operator", "operator.owner@aionos.ai", "Owner / Operator", "Operator@Demo2026"),
]
ROOT = ("Root", "it.consumer@lakshmi.com", "Consumer / Root", "IT@Lakshmi2026")

# A staff role for each service: what it is called, the person who holds it, the service it works on, and the pages it opens
STAFF = [
    {"role": "Marketing", "description": "Runs the Product service: catalog, orders, pricing and bids", "service": "PaaS",
     "user": ("Marketing", "marketing.consumer@lakshmi.com", "Consumer / Marketing", "Marketing@Lakshmi2026"),
     "pages": ["paas/products", "paas/orders", "paas/forecast", "paas/bidding", "paas/pricing", "paas/insights"], "landing": "paas/products"},
    {"role": "Operation", "description": "Runs the Transport service: shipments, return routes and delivery rules", "service": "TaaS",
     "user": ("Operation", "operation.consumer@lakshmi.com", "Consumer / Operation", "Operation@Lakshmi2026"),
     "pages": ["taas/shipments", "taas/returns", "taas/delivery", "taas/insights"], "landing": "taas/shipments",
     "also": ["/saas/return/request/read/v1"]},  # the Return routes page lists approved returns, which is a Support read
    {"role": "Support", "description": "Runs the Support service: tickets, returns, refunds and repairs", "service": "SaaS",
     "user": ("Support", "support.consumer@lakshmi.com", "Consumer / Support", "Support@Lakshmi2026"),
     "pages": ["saas/tickets", "saas/returns", "saas/aftersales"], "landing": "saas/tickets"},
]
CUSTOMER = ("Individual Customer", "individual.customer@gmail.com", "Customer / Individual", "Customer@Lakshmi2026")

STAFF_ACTORS = ("Consumer staff", "System", "AI", "Partner")  # what a role can be given; root-only features stay with the Root

def _ensure_account(name: str, email: str, role: str, portal: str, password: str, tenant_id: str = None) -> str:
    if maas.find_user(email):
        return "kept"
    maas.create_account(name, email, role, portal, password, tenant_id=tenant_id)
    return "created"

def main() -> int:
    ensure_schema()
    tenant = maas.get_tenant_by_name(CONSUMER) or maas.create_tenant(CONSUMER, CONSUMER_TYPE, {"company": {"legal_name": CONSUMER, "industry": "Circular retail"}})
    tid = tenant["tenant_id"]
    report: List[str] = []

    # the consumer has every service
    for service in SERVICE_ORDER:
        registry.set_service_enabled(tid, service, True)
    report.append(f"consumer {CONSUMER}: {len(registry.enabled_paths(tid))} endpoints opted in")

    for name, email, role, password in OWNERS:
        report.append(f"owner    {email}: " + _ensure_account(name, email, role, "Owner", password))
    report.append(f"consumer {ROOT[1]}: " + _ensure_account(ROOT[0], ROOT[1], ROOT[2], "Consumer", ROOT[3], tid))
    report.append(f"customer {CUSTOMER[1]}: " + _ensure_account(CUSTOMER[0], CUSTOMER[1], CUSTOMER[2], "Customer", CUSTOMER[3], tid))

    enabled = registry.enabled_paths(tid)
    views: Dict[str, Any] = {}
    for staff in STAFF:
        existing = next((r for r in role_store.list_roles(tid) if r["name"].lower() == staff["role"].lower()), None)
        role = existing or role_store.create_role(tid, staff["role"], staff["description"])
        name, email, urole, password = staff["user"]
        report.append(f"consumer {email}: " + _ensure_account(name, email, urole, "Consumer", password, tid))
        if not db.one("SELECT 1 AS x FROM role_mails WHERE role_id = CAST(:r AS uuid) AND mail = :m", r=role["role_id"], m=email):
            db.run("INSERT INTO role_mails (role_id, mail, status) VALUES (CAST(:r AS uuid), :m, 'active')", r=role["role_id"], m=email)
        paths = [e["path"] for e in registry.list_endpoints(staff["service"])
                 if not e["owner_side"] and e["actor"] in STAFF_ACTORS and e["path"] in enabled]
        paths += [p for p in staff.get("also", []) if p in enabled and p not in paths]
        role_store.grant_many(tid, role["role_id"], paths)
        views[role["role_id"]] = {"pages": staff["pages"], "landing": staff["landing"]}
        report.append(f"role     {staff['role']}: {len(paths)} {staff['service']} endpoints, opens on {staff['landing']}")

    # the customer storefront, published, with how each role sees the workspace
    template = role_store.get_template(tid) or {"exists": True, "name": "Lakshmi storefront", "layout": {"style": "grid", "hero": True},
                                                 "branding": {"colour": "#1A73E8", "brand_name": CONSUMER}, "sections": [], "version": 1,
                                                 "published": True, "published_at": None, "version_note": "Demo", "role_views": {}}
    template["role_views"] = {**template.get("role_views", {}), **views}
    role_store.save_template(tid, template)
    print("\n".join(report))
    return 0

if __name__ == "__main__":
    sys.exit(main())
