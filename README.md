# AuraCommerce 360 — Decoupled GCP Circular Commerce Web Application

AuraCommerce 360 is an intelligent 360-degree supply-to-disposal circular commerce web application built on Google Cloud Platform serverless infrastructure and foundation models.

---

## 🎨 Theme & Branding
- **Google Design System Palette**: Google Clean aesthetic (Material 3 cards, rounded corners, Google Sans typography).
- **Primary Color**: **Google Teal (`#005F60` / `#00897B`)** paired with Google Blue (`#4285F4`), Red (`#EA4335`), Yellow (`#FBBC04`), and Green (`#34A853`).

---

## 🏛️ Architecture & Hosting Strategy (Image 1 & Image 2)

```
                         AuraCommerce 360 Architecture
                         
    +-----------------------------------------------------------------------+
    |                    FRONTEND (Firebase Hosting)                        |
    |          Google Teal Theme (#005F60) • Single Page App                |
    |                                                                       |
    |    +-----------------+   +--------------------+   +--------------+    |
    |    |   OWNER VIEW    |   |   CONSUMER VIEW    |   | CUSTOMER VIEW|    |
    |    +-----------------+   +--------------------+   +--------------+    |
    +-----------------------------------+-----------------------------------+
                                        |
                             REST APIs / JSON Over HTTP
                                        v
    +-----------------------------------------------------------------------+
    |                   BACKEND (Google Cloud Run API)                      |
    |                   FastAPI Microservices Gateway                       |
    |                                                                       |
    |  +-------------+  +-------------+  +-------------+  +-------------+   |
    |  |  MaaS API   |  |  PaaS API   |  |  TaaS API   |  |  SaaS API   |   |
    |  +-------------+  +-------------+  +-------------+  +-------------+   |
    +-----------------------------------+-----------------------------------+
                                        |
                  +---------------------+---------------------+
                  |                                           |
                  v                                           v
    +---------------------------+               +---------------------------+
    |  GCP Intelligence Layer   |               |      GCP Data Layer       |
    |  - Vertex AI (Gemini)     |               |  - Cloud SQL (Postgres)   |
    |  - TimesFM & TabFM        |               |  - Firestore / BigQuery   |
    +---------------------------+               +---------------------------+
```

### 1. Actor Portals (Image 2 Layout)
- **Owner**: Operates the services — Management as a Service (MaaS), user RBAC, multi-tenant matrix, GCP 3-month budget alerts ($120 cap).
- **Consumer**: Consumes the services — Product as a Service (PaaS) catalog, surplus auctions, TimesFM demand forecasting, Transport as a Service (TaaS) logistics.
- **Customer**: Utilizes services via consumer — Shopping storefront, Customer-to-Multi-Seller Bidding Protocol, Gemini Flash AI assistant, photo return triage.

---

## 🚀 Running Locally (Keyless Preview Mode)

### Backend (Cloud Run Service)
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
- OpenAPI Documentation: `http://localhost:8000/docs`

### Frontend (Firebase Hosting App)
```bash
cd frontend
npm install
npm run dev
```
- App preview URL: `http://localhost:3000`

---

## ☁️ Cloud Deployment Commands

### Deploy Backend to Cloud Run
```bash
cd backend
gcloud run deploy auracommerce-backend --source . --region us-central1 --allow-unauthenticated
```

### Deploy Frontend to Firebase Hosting
```bash
cd frontend
npm run build
firebase deploy --only hosting
```

