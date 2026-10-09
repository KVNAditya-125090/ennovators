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

### Service Layout

Each GCP service from the architecture diagram has its own top-level folder.

| Folder | GCP service | Role |
|--------|-------------|------|
| `firebase_hosting/` | Firebase Hosting | React SPA; `firebase.json` rewrites `/api/**` to Cloud Run |
| `looker_studio/` | Looker Studio | Analytics dashboards (embedded by the SPA via `VITE_LOOKER_STUDIO_URL`) |
| `cloud_run/` | Cloud Run | FastAPI gateway (service and user routers) |
| `vertex_ai/` | Vertex AI | Gemini chat, photo grading, TimesFM forecast |
| `bigquery/` | BigQuery | Demand history (feeds Vertex AI), spend metrics, Looker source |
| `cloud_sql/` | Cloud SQL | Tenants, users, RBAC |
| `firestore/` | Firestore | Products, shipments, support tickets |
| `cloud_storage/` | Cloud Storage | Return-photo uploads (signed URLs) |

Request flow: Firebase Hosting / Looker Studio -> Cloud Run -> Vertex AI -> BigQuery -> Cloud SQL / Firestore / Cloud Storage.

### Users and Services

Every folder is split the same way, following the actor/service diagram:

- `services/` holds logic for the four services: **MaaS** (role access, user listing, databases), **PaaS** (list, sell and buy products), **TaaS** (move goods A to B), **SaaS** (queries, after-sales, repairs).
- `users/` holds what each of the three actors uses: **Owner** (the developer of the product), **Consumer** (consumes the services), **Customer** (utilizes the services via the consumer).

Every GCP folder has all four service folders and all three user folders, so new APIs and features have a place to land:

```
firestore/
  services/
    maas.py  paas.py  taas.py  saas.py          # entry files
    maas/    paas/    taas/    saas/             # feature folders (no __init__.py)
  users/
    owner.py  consumer.py  customer.py          # entry files
    owner/    consumer/    customer/            # feature folders (no __init__.py)
```

- Python: each entry file (`paas.py`, `owner.py`) sits beside a folder of the same name. `service.py` in the folder (`router.py` in `cloud_run/`) holds the logic and `schemas.py` holds Pydantic models. Files with only a docstring are stubs for planned work. The entry file re-exports the folder's main file, so the rest of the code imports `from firestore.services.paas import firestore_paas`. Python would normally let the folder hide the file, so the folder has no `__init__.py` and the entry file sets `__path__` to point at it. Keep both of those when you add features.
- `firebase_hosting/src/` follows the same pattern: `services/paas.js` re-exports `services/paas/index.js`, and `users/owner.js` re-exports `users/owner/api.js`.
- There is no separate `components/` folder in `firebase_hosting/src/`. UI components live in the service or user folder they belong to:

  | Location | Components |
  |----------|------------|
  | `users/owner/` | `OwnerView`, `LookerStudioEmbed` |
  | `users/consumer/` | `ConsumerView` |
  | `users/customer/` | `CustomerView`, `LandingPage` |
  | `services/maas/` | `SignInModal` (role access) |
  | `services/paas/` | `BiddingModal`, `AiAssistantDrawer` |
  | `src/` | `App`, `Navbar` (app shell, shared by all) |

- `looker_studio/` uses a `README.md` per folder in place of code.

The table lists what each file contains today:

| Folder | `services/` | `users/` |
|--------|-------------|----------|
| `cloud_run/` | maas, paas, taas, saas routers (`/api/v1/<service>/...`) | owner, consumer, customer routers (`/api/v1/<user>/...`) |
| `firebase_hosting/src/` | maas.js, paas.js, taas.js, saas.js API clients | owner, consumer, customer views plus each one's api.js |
| `vertex_ai/` | saas (chat, photo grading), paas (forecast) | consumer, customer |
| `bigquery/` | maas (budget, workspace usage), paas (demand history) | owner, consumer |
| `cloud_sql/` | maas (tenants, users, workspaces) | owner, consumer |
| `firestore/` | paas (products), taas (shipments), saas (tickets) | consumer, customer |
| `cloud_storage/` | saas (return photos) | customer |

The data services are keyless mocks; each class is the swap point for the real client library.

### 1. Actor Portals (Image 2 Layout)
- **Owner**: The developer of the product. Sees every consumer, their details and costs, and switches any API on or off for any consumer at any time. Does not track consumers' orders or tickets.
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

### Firebase Hosting (SPA)
```bash
cd firebase_hosting
npm install
npm run dev
```
- App preview URL: `http://localhost:3000`

---

## 🔐 Sign-in (preview)

There is one sign-in form. The account decides the role, and the role decides which portal opens, so there is no role picker and no role switcher after sign-in.

| Account | Password | Opens |
|---------|----------|-------|
| `admin@auracommerce.io` | `Owner@123` | Owner portal |
| `seller@greencycle.com` | `Seller@123` | Consumer portal |
| `customer@gmail.com` | `Customer@123` | Customer storefront |

These are demo accounts held in `cloud_sql/services/maas/service.py` and checked by `POST /api/v1/maas/auth/login`. The API does not issue sessions or tokens yet, so replace this with real authentication (for example Firebase Authentication) before any production use.

---

## ☁️ Cloud Deployment Commands

### Deploy to Cloud Run
```bash
# from the program root (buildpacks use ./requirements.txt)
gcloud run deploy auracommerce-backend --source . --region us-central1 --allow-unauthenticated \
  --set-build-env-vars GOOGLE_ENTRYPOINT="uvicorn cloud_run.main:app --host 0.0.0.0 --port \$PORT"
```

### Deploy to Firebase Hosting
```bash
cd firebase_hosting
npm run build
firebase deploy --only hosting
```

