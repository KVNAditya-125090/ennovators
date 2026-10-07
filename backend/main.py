"""
AuraCommerce 360 Backend Service Core
Target Deployment: Google Cloud Run
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import maas, paas, taas, saas

app = FastAPI(
    title="AuraCommerce 360 API Gateway",
    description="Intelligent End-to-End Circular Retail Platform API Gateway (MaaS, PaaS, TaaS, SaaS)",
    version="1.0.0"
)

# Enable CORS for Firebase Hosting frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Service Routers
app.include_router(maas.router)
app.include_router(paas.router)
app.include_router(taas.router)
app.include_router(saas.router)

@app.get("/")
def root():
    return {
        "title": "AuraCommerce 360 API Gateway",
        "status": "Online",
        "gcp_hosting_target": "Cloud Run (Serverless)",
        "documentation": "/docs",
        "service_modules": ["MaaS", "PaaS", "TaaS", "SaaS"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

