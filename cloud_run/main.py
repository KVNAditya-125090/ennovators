"""
Lakshmi Backend Service Core
Target Deployment: Google Cloud Run
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cloud_run.services import maas, paas, taas, saas
from cloud_run.users import owner, consumer, customer
from cloud_run import gate, sync, media
from cloud_run.auth import IdentityMiddleware
from cloud_run.unit_of_work import UnitOfWorkMiddleware
from cloud_sql import db as sql_db
from cloud_sql.schema import ensure_schema
import logging

log = logging.getLogger("lakshmi")

app = FastAPI(
    title="Lakshmi API Gateway",
    description="Intelligent End-to-End Circular Retail Platform API Gateway (MaaS, PaaS, TaaS, SaaS)",
    version="1.0.0"
)

# Only the Firebase Hosting site (and local development) may call the API from a browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agent-lakshmi.web.app", "https://agent-lakshmi.firebaseapp.com", "http://localhost:3000"],
    allow_credentials=False,  # sign-in is a Bearer token, not a cookie
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-Id", "X-User-Name", "X-User-Email"],  # X-User-Email is dropped by IdentityMiddleware; it only has to pass the preflight
)

# Who is calling comes only from the signed token: any X-User-Email the caller sends is dropped
app.add_middleware(IdentityMiddleware)
# One unit of work per request: records are read from Firestore as they are needed and written back when the request ends well
app.add_middleware(UnitOfWorkMiddleware)

@app.on_event("startup")
def prepare_database() -> None:
    if sql_db.configured():
        ensure_schema()
    else:
        log.warning("DB_PASSWORD is not set: running without a database")

# Keep the three portals in step: a change to access or the interface bumps a counter they all watch
sync.install(app)
app.include_router(sync.router)
app.include_router(media.router)

# Register Service Routers (MaaS, PaaS, TaaS, SaaS)
app.include_router(maas.router)
app.include_router(paas.router)
app.include_router(taas.router)
app.include_router(saas.router)

# The gate: every catalog endpoint, checked on each call
app.include_router(gate.router)

# Register User Routers (Owner, Consumer, Customer)
app.include_router(owner.router)
app.include_router(consumer.router)
app.include_router(customer.router)

@app.get("/")
def root():
    return {
        "title": "Lakshmi API Gateway",
        "status": "Online",
        "gcp_hosting_target": "Cloud Run (Serverless)",
        "documentation": "/docs",
        "service_modules": ["MaaS", "PaaS", "TaaS", "SaaS"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("cloud_run.main:app", host="0.0.0.0", port=8000)

