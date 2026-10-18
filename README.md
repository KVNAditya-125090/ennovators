# Lakshmi — the 360° Commerce Platform

Lakshmi (earlier called AuraCommerce 360) is an end-to-end commerce application built by Team Ennovators at AIONOS for the H2S Google AI hackathon. It lets anyone sell, buy, deliver and support products online, with AI helping at every step. Its main focus is **local products**: a small seller in a town or village can list what they make, reach buyers across the country in the buyer's own language, and run the whole business from one place. The same platform also works inside a company for its own commerce.

Lakshmi is designed for common Indian citizens, in towns and villages, and especially for women who run or want to start a small business. Everything is meant to be simple to use: plain words, voice as well as typing, and a choice of nine languages.

Frontend: https://agent-lakshmi.web.app/

---

## 1. The five things Lakshmi is built around

### 1.1 AI-based interactions
Each part of the shop has its own assistant: shopping, delivery, support, and account help. A shopper can type or speak, and the assistant answers in the shopper's own language, in a few short, plain sentences, using only the shop's real facts (prices, stock, products, delivery rules, policies). If the facts don't answer the question, it says so and suggests contacting the store. It never invents a price, a date or a product.

Four ways to talk to the assistants, chosen in Settings: text to text, text to speech, speech to text, and speech to speech. Voice uses the browser's own speech features (Chrome or Edge work best).

Other AI features: grading a returned item from a photo (condition grade A to D, how much value can be recovered, and where it should go next), AI planning of delivery routes, vehicles, arrival times and delivery slots, and AI negotiation of prices (see 1.3).

### 1.2 Personalized recommendations
Lakshmi suggests products from what a shopper has put in the cart or wishlist, ordered or bid on, and falls back to popular products, greenest first. It also offers sustainable alternatives and "frequently bought together" items. The seller can:
- group customers into segments (repeat buyers, high value, new, gone quiet) from real order history, and send an offer to a segment, which then shows up as that customer's personal price on products (never below the seller's bidding floor);
- get bundle suggestions (products most often bought together, priced a few percent under buying them separately and never under their floors) and create bundles;
- limit which of a shopper's signals (cart, wishlist, orders, bids) the recommendations may use, and for how many days.

A shopper can see why something was recommended, and can reset their profile. Staff can build a customer's profile (favourite categories, price band, average order) from their activity.

### 1.3 Dynamic pricing and price bidding
**Dynamic pricing.** For one product, Lakshmi suggests a price from the seller's own records:
- demand: how much sold in the last 30 days against what is in stock,
- stock cover: how many days of stock are left at the current selling rate,
- condition: refurbished and used goods sit a little below new ones,
- bid pressure: the prices shoppers actually agreed in bids.

Each factor gives a percentage nudge and a reason in plain words. The result is held inside the seller's own rules: a largest allowed change from the original list price and a minimum margin above the bidding floor. Staff then apply or ignore the suggestion. A suggestion cannot be applied twice or after the price has changed.

Segment offers add personal prices on top of this, and green credits are a second kind of price benefit: the seller sets how many credits a dollar earns and what a credit is worth.

**Price bidding.** Three ways to bargain:
- **AI-assisted bid.** The shopper makes an offer and the AI bot bargains for the seller. It never goes below the seller's bidding floor and gives up after five counters. When a price is agreed, the deal is handed to the seller's staff, the seller's root account gets a mail, and staff confirm or reject it, with a reason. Staff can see every deal waiting for a decision in a list. The seller's **bid rules** are enforced: the lowest price and deepest discount the bot may agree, how many counters it makes, the range of opening offers a shopper may make (overall or per category), how many hours a bid stays open, and the lowest seller rating and stock a multi-seller room needs.
- **Human bid.** The shopper bargains directly with the seller's staff.
- **Multi-seller bid.** The shopper states a budget; eligible sellers make offers, the offers are ranked on price, seller rating, delivery time and how much new manufacturing the choice avoids, and the best fit within the budget wins.

### 1.4 Environmental intelligence and sustainable operations
Lakshmi is built for circular commerce: reuse, refurbish, repair, recycle.
- **Product passport and environmental score** for each product (with a QR/scan option), including carbon footprint and recyclable share.
- **Green credits** that shoppers earn and redeem.
- **Carbon footprint of delivery and of each offer**, so the shopper can choose the greener option.
- **Green delivery planning:** the cheapest, fastest, shortest or greenest route, and a vehicle chosen for the load (e-cargo bike, electric van, diesel van, truck, rail, air), with CO₂ per kilometre taken into account.
- **Green route recommendations:** for any load between two places, the lowest-emission vehicle that can carry it, what it saves against a diesel van, the reasons in plain words, and a one-time record of the saving against a real shipment that joins the impact ledger.
- **Reverse logistics:** returns and end-of-life goods are routed to resale, refurbishment, parts harvesting, donation or certified recycling, and recycling requests and pickups can be booked.
- **Impact reports** for the seller: Product, Transport and Support reports and a net report, each figure with an id, exportable as CSV for ESG reporting, and each with a plain note on where the number comes from, how far to trust it and what it is compared against. The seller can also record baselines and savings, and the footprint of the AI itself is shown.

### 1.5 Local marketing and a global reach
- **Nine languages** across the whole app: English, Hindi, Telugu, Tamil, Kannada, Marathi, Bengali, Gujarati and Malayalam. The menu, sign-in, settings and assistants are translated, the assistants answer in the chosen language, and voice uses it. The choice is saved with the account.
- **Listing translation.** A seller's product name and description can be translated into any of the nine languages with Gemini. The translation is kept with the product, so asking again for an unchanged listing costs nothing. Support tickets and replies can be translated the same way.
- **Local connection.** Sellers add their stores; shoppers find the nearest store, see stock per store, and get address checks and service areas for delivery, using Google Maps.
- **Open to the whole country (and beyond).** Any seller can use the platform to reach buyers anywhere. The seller chooses which of the nine languages its shoppers may pick (a shopper cannot pick one the store does not offer), whether it operates locally or globally and in which regions, which currencies it uses, and its return window and refund method for each region.

---

## 2. Who uses it

Lakshmi is white-labelled: the platform has an **owner**, who runs it, **consumers**, who are businesses that run their shop on it, and **customers**, who buy from one consumer's branded store.

| User | Who they are | What they do |
|------|--------------|--------------|
| **Owner** | The team that runs the platform. Roles: Manager, Developer, Operator. | Onboards consumers, decides which features each one gets and at what rate limit and price, watches health, cost and revenue, and brokers partnerships between consumers. |
| **Consumer** | A business that sells on the platform (the demo consumer is "Lakshmi Demo Retail"). Its **Root** account decides what each internal role (Manager, Seller, Dispatcher or a custom role) can see and do. | Manages products, stock, orders, prices, bids, deliveries, support tickets and returns, and designs the storefront its customers see. |
| **Customer** | An individual or business buying from one consumer's store. Never sees the Owner. | Browses, searches (text, voice, image), shops, bids, tracks orders, returns, reviews, and talks to the assistants. |

---

## 3. The four services

Every feature belongs to one of four modules. A consumer opts into only the ones it needs, and can rely on other consumers for the rest (for example, sell products and use a partner for transport).

| Service | Name | What it covers |
|---------|------|----------------|
| **MaaS** | Management | Accounts, roles and permissions, storefront templates, opt-in, billing, audit, impact, language, region and currency. Required by every consumer. |
| **PaaS** | Product | Catalogue, stock, orders, bidding and auctions, dynamic pricing, promotions, forecasts, recommendations, listing translation. |
| **TaaS** | Transport | Shipments, AI delivery planning, return routes, delivery rules, service areas, delivery carbon figures. |
| **SaaS** | Support | Tickets, returns and refunds, photo grading, repairs, trade-ins, recycling, ticket translation. |

The platform has **417 features**, and each one is a single API endpoint with a clear path such as `/paas/bid/ai/start/v1`. The full list is in `cloud_sql/services/maas/endpoint_catalog_v1.csv`. Splitting features this finely keeps access tight, security simple, costs measurable and each piece easy to maintain.

---

## 4. How it works

```
 Browser (React app, Firebase Hosting)
        |  REST / JSON
        v
 FastAPI gateway on Cloud Run  ->  the gate  ->  endpoint handlers
        |
        +-- Vertex AI (Gemini)      chat, photo grading, translation
        +-- Cloud SQL               accounts, roles, opt-ins, audit log
        +-- Firestore               products, orders, shipments, tickets, shoppers' data
        +-- BigQuery                usage, spend, sales and demand history
        +-- Cloud Storage           return photos and product media
        +-- Google Maps             routes, geocoding, places
```

**The gate.** Every call passes five checks in order: (1) the caller is identified from a signed sign-in token, never from a header the caller sends; (2) the consumer has opted into that feature (set by the Owner); (3) the caller's internal role is allowed it (set by the consumer's Root); (4) the call is within its rate limit; (5) the call is written to the audit log, allowed or refused.

**Security basics.** Passwords are stored only as salted `scrypt` hashes, five wrong passwords lock an account for 15 minutes, and sign-in returns an 8-hour signed token. Each customer has a separate account per consumer and sees only that consumer's brand. Customer data is kept per shop and per shopper.

**Physical and digital together.** A customer can reserve or pre-book online and collect offline, confirmed by a code or by staff, with every step recorded as data.

---

## 5. Technology

- **Frontend:** React, Vite and Tailwind, hosted on Firebase Hosting. Google-style design (Material 3 cards, Google Sans, teal `#005F60` / `#00897B` with Google blue, red, yellow and green).
- **Backend:** Python and FastAPI on Google Cloud Run.
- **AI:** Gemini on Vertex AI for the assistants, photo grading and translation. Delivery planning, bidding, pricing and recommendations are rule-based and worked out from the seller's own records.
- **Data:** Cloud SQL (PostgreSQL), Firestore, BigQuery and Cloud Storage.
- **Maps:** Google Maps Routes, Geocoding and Places, with a daily safety cap on use.

Code layout: each Google Cloud service has its own top-level folder (`cloud_run`, `cloud_sql`, `firestore`, `bigquery`, `vertex_ai`, `cloud_storage`, `maps`, `firebase_hosting`), and inside each, `services/` holds the logic for the four services and `users/` what each of the three users works with.

---

## 6. Where the project stands

Lakshmi is a working prototype: a complete interface over a real backend on Google Cloud, with the main business flows working end to end. All 417 features are in the interface behind the access gate.

**Working end to end (206 features).** Real logic over the consumer's own data, or real Gemini calls:
- the shopping, delivery, support and account assistants, in nine languages, with text and voice;
- shopping: catalog, search, cart, wishlist, orders, tracking, reviews, tickets, returns, reservations;
- all three kinds of bidding, the AI hand-off to the seller, and the seller's bid rules;
- dynamic pricing (rules, suggest, apply), segment offers, bundles, profiles and recommendations;
- impact reports, recorded savings, CSV export and the notes behind each figure;
- green route recommendations, delivery planning, carbon figures, product passports, environmental scores and green credits;
- listing and ticket translation, language, region, currency and regional return-policy settings, stores and nearby-store search;
- roles, permissions, storefront customization, and the access gate itself.

**Working with a placeholder part (22 features).** These work, but one part returns a stand-in value: the server-side voice-input path of the assistants (voice itself works through the browser), payment processing, coupons, trade-in valuation, return-risk and future-value quotes, drop-off status, and customer login by the older path.

**In the interface, not yet wired to real logic (155 customer and consumer features, plus all 34 Owner features).** They accept input and answer with a clearly marked preview response (`"preview": true`), so every screen can be used today. They are mostly in these groups: surplus auctions, partner and refurbisher bidding, human-bid responses, bid guardrails, voice and image product search, assistant and grading settings, passport generation and transfer, origin verification, recycling certificates and lifespan estimates, delivery-price suggestions, shelf-life pricing, currency conversion, and the Owner portal's actions.

Still to do before production: the groups above, token-based sign-in for invited team members, persistent shared rate limits, automated tests, review of the interface translations by a native speaker of each language, real seller accounts in place of the four demo sellers in multi-seller bidding, and PDF export of impact reports.

Estimates and assumptions are stated where they are used: delivery and impact figures are estimates against a named baseline, not measurements.

---

## 7. Running and deploying

**Locally** (the Google Cloud services need credentials, or the matching settings, to work):

```bash
pip install -r requirements.txt
uvicorn cloud_run.main:app --reload --port 8000     # API docs at http://localhost:8000/docs

cd firebase_hosting && npm install && npm run dev   # app at http://localhost:3000
```

Demo accounts (Owner, Consumer roles and Customer) are shown on the sign-in screen. Create them with `python -m cloud_sql.seed_demo`, the demo records with `python -m firestore.seed_demo_data`, and the Owner's charts with `python -m bigquery.seed_demo`.

**Deploy** (PowerShell; keep the single quotes so `$PORT` is left alone):

```powershell
gcloud run deploy lakshmi-backend --source . --region us-central1 --allow-unauthenticated --set-build-env-vars 'GOOGLE_ENTRYPOINT=uvicorn cloud_run.main:app --host 0.0.0.0 --port $PORT'

cd firebase_hosting
npm run build
firebase deploy --only hosting
```

The front end calls the Cloud Run service directly: its address is set at build time in `firebase_hosting/.env.production` (`VITE_API_BASE_URL`), and the API allows calls only from the hosted site and local development. Hosting serves `dist/` and sends every path to `index.html`. `--allow-unauthenticated` is fine for demo data; the gate and sign-in tokens still protect every feature call.
