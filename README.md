# Lakshmi — Decoupled GCP Circular Commerce Web Application

Lakshmi is a 360° commerce platform built as a React single-page app (Firebase Hosting) over a FastAPI gateway (Cloud Run). It has four services and three kinds of user.

> **Status: working preview.** Every one of the 416 catalog features is in the interface, behind one access gate. 157 have a real handler and 259 answer through preview stand-ins. All data is in memory and the Google Cloud services are keyless mocks. See [Project status](#project-status).

Related docs:

| File | What it holds |
|------|---------------|
| [functionalities.md](functionalities.md) | Every feature by user (Owner, Consumer, Customer): its endpoint, who does it, and whether it is built |
| [checkpoints.md](checkpoints.md) | What was deliberately left open, with the code that holds each stopgap |
| `looker_studio/**/README.md` | Dashboard specs (no code) |

---

## Theme & Branding
- **Google Design System palette**: Google Clean aesthetic (Material 3 cards, rounded corners, Google Sans typography).
- **Primary colour**: Google Teal (`#005F60` / `#00897B`) with Google Blue (`#4285F4`), Red (`#EA4335`), Yellow (`#FBBC04`) and Green (`#34A853`).

---

## Architecture

```
                         Lakshmi Architecture

    +-----------------------------------------------------------------------+
    |                    FRONTEND (Firebase Hosting)                        |
    |          React + Vite + Tailwind • Single Page App                    |
    |                                                                       |
    |    +-----------------+   +--------------------+   +--------------+    |
    |    |   OWNER VIEW    |   |   CONSUMER VIEW    |   | CUSTOMER VIEW|    |
    |    +-----------------+   +--------------------+   +--------------+    |
    +-----------------------------------+-----------------------------------+
                                        |
                             REST APIs / JSON Over HTTP
                                        v
    +-----------------------------------------------------------------------+
    |                   BACKEND (Google Cloud Run)                          |
    |        FastAPI gateway: routers + the gate + endpoint handlers        |
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
    |  - Vertex AI (Gemini)     |               |  - Cloud SQL, Firestore   |
    |  - TimesFM & TabFM        |               |  - BigQuery, Cloud Storage|
    +---------------------------+               +---------------------------+
```

Request flow: Firebase Hosting / Looker Studio -> Cloud Run -> Vertex AI -> BigQuery -> Cloud SQL / Firestore / Cloud Storage.

### The four services

| Service | Name | What it covers |
|---------|------|----------------|
| **MaaS** | Management | Accounts, roles and permissions, interface templates, opt-in, billing, audit, impact |
| **PaaS** | Product | Catalogue, stock, orders, bidding and auctions, pricing, promotions, forecasts |
| **TaaS** | Transport | Shipments, AI delivery planning, return routes, delivery rules |
| **SaaS** | Support | Tickets, returns and refunds, grading, repairs, trade-ins, recycling |

### The three users

- **Owner**: runs the platform. Onboards consumers, decides which endpoints each gets and at what rate limit and price, and watches health, cost and revenue. Roles: Manager, Developer, Operator.
- **Consumer**: a company that runs its business on the platform (demo: GreenCycle Refurbishers). Its **Root** account decides what each internal role (Manager, Seller, Dispatcher, or a custom role) can see and do.
- **Customer**: an individual or business buying from one consumer's branded store. Never sees the Owner.

### The feature catalog

Every feature is one endpoint of `cloud_sql/services/maas/endpoint_catalog_v1.csv` (416 rows; 34 Owner, 272 Consumer, 110 Customer). Parameters for each are drafted in `cloud_sql/services/maas/endpoint_params.py`. The registry in `cloud_sql/services/maas/endpoints.py` is seeded from the CSV and holds opt-ins, rate limits, prices and the audit log.

### The gate

`cloud_run/gate.py` exposes every catalog endpoint at `/api<catalog path>`. A call passes these checks in order:

1. The caller names a consumer (`X-Tenant-Id`) and a person (`X-User-Email`).
2. The consumer is opted into the endpoint (set by the Owner).
3. The caller's internal role is allowed it (set by the Root on *Roles and Team*). Skipped for Customer endpoints, where shoppers have no roles.
4. The call is within the endpoint's rate limit.
5. The call is written to the audit log, allowed or refused.

A call that passes runs its handler. An endpoint with no handler answers `501 not_implemented`.

### Handlers

| Module | Holds |
|--------|-------|
| `cloud_run/handlers.py` | Real Consumer handlers, registered by catalog path |
| `cloud_run/customer_handlers.py` | Customer handlers: account, cart, wishlist, orders, tickets, bids, reviews, assistants. Data is kept per (consumer, shopper) |
| `cloud_run/preview.py` | Stand-ins for Owner and Consumer features with no real handler. They record the call and echo it back with `"preview": true`. A real handler always replaces one |

---

## Project Layout

Each GCP service has its own top-level folder. Every folder is split the same way, following the actor/service diagram:

- `services/` holds the logic for the four services (MaaS, PaaS, TaaS, SaaS).
- `users/` holds what each of the three users (Owner, Consumer, Customer) works with.

```
program/
  README.md  functionalities.md  checkpoints.md  requirements.txt  .gcloudignore
  cloud_run/          FastAPI app, gate, handlers, routers   (the backend entry point)
  cloud_sql/          Tenants, users, the endpoint registry and catalog
  firestore/          Products, shipments, tickets, consumer operations
  bigquery/           Usage, spend and demand history
  vertex_ai/          Gemini chat, photo grading, forecasts, AI delivery planner
  cloud_storage/      Return-photo uploads
  firebase_hosting/   React SPA (Vite, Tailwind)
  looker_studio/      Dashboard specs (README per folder, no code)
```

| Folder | Contents today |
|--------|----------------|
| `cloud_run/` | `main.py` (app), `gate.py`, `access.py` (who may call what), `health.py` (per-endpoint health), `handlers.py`, `customer_handlers.py`, `preview.py`; routers in `services/<svc>/router.py` (`/api/v1/<service>/...`) and `users/<user>/router.py` (`/api/v1/<user>/...`) |
| `cloud_sql/` | `services/maas/`: `service.py` (tenants, users, demo accounts), `endpoints.py` (registry, opt-in, limits, prices, audit), `endpoint_params.py`, `endpoint_catalog_v1.csv`. Other service/user folders are stubs |
| `firestore/` | `services/paas` (products), `services/taas` (shipments), `services/saas` (tickets), `users/consumer/operations.py` (roles, role permissions, template, settings, products, orders, shipments) |
| `bigquery/` | `services/maas` (budget, usage, billing figures), `services/paas` (demand history), `users/owner`, `users/consumer` |
| `vertex_ai/` | `services/saas` (photo grading), `services/paas` (forecast), `services/taas/planner.py` (route, vehicle, ETA and slot planning), `users/consumer`, `users/customer` |
| `cloud_storage/` | `services/saas`, `users/customer` (return photos). Other folders are stubs |

### Python layout rule

Each entry file (`paas.py`, `owner.py`) sits beside a folder of the same name. `service.py` in the folder (`router.py` in `cloud_run/`) holds the logic and `schemas.py` holds Pydantic models. Files with only a docstring are stubs for planned work. The entry file re-exports the folder's main file, so the rest of the code imports `from firestore.services.paas import firestore_paas`. Python would normally let the folder hide the file, so the folder has no `__init__.py` and the entry file sets `__path__` to point at it. **Keep both of those when you add features.**

### Frontend layout (`firebase_hosting/src/`)

Follows the same pattern: `services/paas.js` re-exports `services/paas/index.js`, and `users/owner.js` re-exports `users/owner/api.js`. There is no separate `components/` folder; components live with the service or user they belong to.

| Location | Contents |
|----------|----------|
| `App.jsx`, `Navbar.jsx`, `main.jsx`, `router.js`, `layout.js` | App shell shared by all users. `router.js` maps plain addresses to pages |
| `services/http.js` | Shared request helper |
| `services/maas/` | `SignInModal`, `session.js` |
| `services/paas/` | `BiddingModal`, `AiAssistantDrawer` |
| `services/features/FeatureCards.jsx` | Runnable feature cards built from an endpoint's parameters (used by Owner, Consumer and Customer) |
| `users/owner/` | `OwnerView`, `OwnerNav`, `Analytics`, `Endpoints`, `Operations`, `Pages`, `charts`, `LookerStudioEmbed` |
| `users/consumer/` | `ConsumerView`, `ConsumerNav`, per-service pages (`MaasPage`, `PaasPage`, `TaasPage`, `SaasPage`), `RolesAndTeam`, `Customize`, `DeliveryPlanner`, `MoreFeatures`, `CommandPalette`; `featureCatalog.js` maps features with no screen of their own to a page |
| `users/customer/` | `CustomerView`, `CustomerNav`, `LandingPage`, `Storefront`, `QueryForm`; `features.js` groups the Customer features into Shop, Delivery, Support and Account |

### Addresses

Every page has a plain address, with no `#`: `/<user>/<role>/<service>/<category>/<more>`. For example `/owner/manager/maas/monitor/paas`, `/consumer/root/taas/shipments`, `/customer/individual/paas/shop`. A Consumer feature can be opened directly, for example `/consumer/root/maas/services/api-key/list`. Ctrl+K searches every Consumer page and feature.

---

## Running Locally (Keyless Preview Mode)

No Google Cloud credentials are needed.

### Backend (Cloud Run service)

Run from the program root (the folder holding `cloud_run/`):

```bash
python -m venv venv
# On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn cloud_run.main:app --reload --port 8000
```

- OpenAPI documentation: `http://localhost:8000/docs`
- All state is in memory. A restart, or a file save with `--reload`, puts everything back to the demo values.

### Frontend (Firebase Hosting SPA)

```bash
cd firebase_hosting
npm install
npm run dev
```

- App: `http://localhost:3000`. Vite proxies `/api` to `http://localhost:8000`.
- Optional: set `VITE_LOOKER_STUDIO_URL` in `firebase_hosting/.env.local` to embed a Looker Studio report in the Owner console.

---

## Sign-in (preview)

There is one sign-in form. The account decides the role, and the role decides which portal opens, so there is no role picker and no role switcher after sign-in.

| Account | Password | Opens |
|---------|----------|-------|
| `admin@auracommerce.io` | `Owner@123` | Owner portal (Manager) |
| `developer@auracommerce.io` | `Developer@123` | Owner portal (Developer) |
| `operator@auracommerce.io` | `Operator@123` | Owner portal (Operator) |
| `seller@greencycle.com` | `Seller@123` | Consumer portal (Root of GreenCycle Refurbishers) |
| `rahul@greencycle.com` | `Manager@123` | Consumer portal (Manager role) |
| `anika@greencycle.com` | `Seller@123` | Consumer portal (Seller role) |
| `priya@greencycle.com` | `Dispatcher@123` | Consumer portal (Dispatcher role) |
| `customer@gmail.com` | `Customer@123` | Customer storefront (Individual) |

Staff and Owner demo accounts are held in `cloud_sql/services/maas/service.py` and checked by `POST /api/v1/maas/auth/login`. Customers register and sign in per consumer through the Customer endpoints (`/maas/customer-account/*`).

**The API issues no sessions or tokens.** The gate trusts the `X-Tenant-Id` and `X-User-Email` headers as sent, so anyone can claim to be anyone. Replace this with real authentication (for example Firebase Authentication) before any production use.

---

## Project status

| User | Features | Real handler | Preview stand-in |
|------|---------:|-------------:|-----------------:|
| Owner | 34 | 0 | 34 |
| Consumer | 272 | 66 | 206 |
| Customer | 110 | 91 | 19 |
| **Total** | **416** | **157** | **259** |

"Real handler" means working logic over in-memory demo data. Still open before production (details in [checkpoints.md](checkpoints.md)):

- Real handlers for the 259 stand-in features, including all 34 Owner features.
- Real authentication with tokens (A1) and the missing gate checks: customer enablement, AI/system step limits, partner links, wrong-actor (A3 to A6).
- Real Google Cloud clients behind `cloud_sql/`, `firestore/`, `bigquery/`, `vertex_ai/` and `cloud_storage/`. Today each is a keyless mock, and `requirements.txt` has no Google client libraries. The AI grading and planning are mock or rule-based.
- Persistent storage, a shared rate-limit store, and a stored audit log (C1, D1, D2).
- Tests. None are written yet (F7).

---

## Cloud Deployment

### Deploy to Cloud Run

```bash
# from the program root (buildpacks use ./requirements.txt)
gcloud run deploy auracommerce-backend --source . --region us-central1 --allow-unauthenticated \
  --set-build-env-vars GOOGLE_ENTRYPOINT="uvicorn cloud_run.main:app --host 0.0.0.0 --port \$PORT"
```

`--allow-unauthenticated` is only acceptable while the app is a preview with demo data.

### Deploy to Firebase Hosting

```bash
cd firebase_hosting
npm run build
firebase deploy --only hosting
```

`firebase.json` serves `dist/`, rewrites `/api/**` to the Cloud Run service `auracommerce-backend` (region `us-central1`), and sends every other path to `index.html`.
