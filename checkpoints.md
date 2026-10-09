# Checkpoints

Things deliberately left open while the Owner console and the gate were built. Each one is tied to the endpoints or feature it belongs to, so it can be picked up when that feature is built. When a feature's endpoints get their handlers, go through its checkpoints before calling it done, then tick them off here.

Paths are catalog paths from `endpoint_catalog_v1.csv`. "Where" points to the code that holds the stopgap.

## How the preview works today (read first)

- The catalog (409 endpoints) is seeded from the CSV: `cloud_sql/services/maas/endpoints.py`.
- Every endpoint is reachable at `/api<catalog path>` through the gate: `cloud_run/gate.py`. A call that passes returns `501 not_implemented`.
- The Owner opts consumers in or out, and sets rate limit and price per endpoint: Owner console, service pages.
- All state is in memory. A backend restart (or a file save, with `--reload`) puts everything back to the demo values.

---

## Checkpoint, 9 Oct 2026: Owner and Consumer features against the feature list

The feature list is `endpoint_catalog_v1.csv`: every feature is an endpoint. **Every Owner and Consumer feature in it is now in the interface.** Customer, AI, System and Partner features are not part of this checkpoint.

- ✅ **Built:** a real handler in `cloud_run/handlers.py` and its own screen. Works now.
- 🖥️ **In the interface, needs the backend:** a feature card on the page named below, with a form built from its parameters. It is answered by a preview stand-in (`cloud_run/preview.py`) that records the change, or for a read shows what was recorded. Every answer says `"preview": true`, and nothing real happens (no mail, no payment, no session). To integrate one, write its handler: a real handler always replaces the preview. When it gets a screen of its own, remove its line from `featureCatalog.js`.

| Portal | Features in the list | ✅ Built | 🖥️ In the interface, needs the backend |
|---|---|---|---|
| Owner (manager, developer, operator) | 32 | 0 | 32 |
| Consumer root | 91 | 29 | 62 |
| Consumer staff | 109 | 37 | 72 |
| **Total** | **232** | **66** | **166** |

### Where to find them

- **Owner:** the new **Operations** item in the Owner menu, with tabs Onboarding, Consumer tickets, Partners, Owner team, Developer, Audit and impact, and Account. All three Owner roles see the same. API: `GET /api/v1/owner/features`, and run one at `/api/v1/owner/features/run<catalog path>` (Owner sign-in needed).
- **Consumer:** new pages Services and endpoints, Partners, Owner tickets, Stores and locations, Data and audit, Impact, Account and sign-in (Management), Bidding, Pricing and promotions, Insights (Product), and Repairs and recycling (Support). Existing pages have a "More features" section for the rest. Ctrl+K search finds every one.
- **Root control still applies:** a role sees a feature only if the workspace opted into it, the root allowed it on Roles and Team, and its page is ticked on Customization. The gate enforces the same.

### Added 9 Oct 2026: AI delivery planning in TaaS

Seven new catalog features (in both copies of `endpoint_catalog_v1.csv`, parameters in `endpoint_params.py`). Each one is opt-in like any other feature and shows only to roles the root allows. The Dispatcher role has them by default.

| Endpoint | What it does |
|---|---|
| `/taas/route/optimize/recommend/v1` | Route by shortest, fastest, cheapest or greenest, with extra stops; compares expressway, national highway and toll-free roads |
| `/taas/vehicle/recommend/v1` | Vehicle type from load (kg, litres) and distance: e-cargo bike, electric van, diesel van, truck, rail plus electric last mile, air express. Says why the others are ruled out |
| `/taas/delivery/eta/predict/v1` | Delivery date and time with an earliest and latest time and a confidence. Accounts for the cut-off, Sunday, driver rest, Monday delays and delivery hours |
| `/taas/delivery/slot/recommend/v1` | Delivery slots ranked by how likely they are to be on time |
| `/taas/explain/decision/read/v1` | The plain-language reason for any of the above |
| `/taas/recommendation/accept/v1` | Apply the AI pick to the shipment |
| `/taas/recommendation/override/v1` | Apply another option; a reason is required and kept with who decided and when |

- **Screen:** Transport → Shipments → a shipment's menu → **Plan delivery with AI**. Each part shows its options, the AI pick, why it was picked (summary, factors, confidence, data sources), then Accept or Choose another. The chosen vehicle, route and slot show under the carrier, and the predicted time goes in Arrives.
- **Model:** `vertex_ai/services/taas/planner.py` is a rule-based preview: distances between known city centres, typical speeds, costs and emissions. Replace it with the real model (Vertex AI, maps and traffic data) and keep the response shape: `options`, `recommended`, `explanation {summary, factors, confidence, data_sources}`.
- **Handlers:** in `cloud_run/handlers.py`, so these count as ✅ built (they work now, with preview figures).
- **To do with the backend:** real road distances and traffic, the fleet the consumer actually has, and storing decisions (they are in memory). The `list_item` numbers for the new rows (38, 36, 35) are my guesses at the master-list items; check them.

### Also working (outside the catalog)

- Owner console: dashboard with analytics, visitor queries, the consumer list with details and tickets, per-endpoint opt-in, rate limits and prices, Monitor, Telemetry.
- From the Interface and Navigation Plan: Transport split into 4 pages, Ctrl+K search, Customization per role (applied to the real role user), the customer storefront builder. **Not done:** the sign-in redesign (demo accounts still in the main card, no role confirmation line).
- Gate: purchased check, role-permission check (A2), rate limit and audit. Callers must be named and belong to the consumer, and the Owner API needs an Owner.

### Owner features

| Endpoint | Role | Feature | Status | Where |
|---|---|---|---|---|
| `/maas/root-account/provision/v1` | manager | Root account is provisioned when a Consumer is onboarded | 🖥️ | Operations → Onboarding |
| `/maas/partner/link/approve/v1` | operator | Record a brokered partner link after settlement | 🖥️ | Operations → Partners |
| `/maas/partner/commission/policy/set/v1` | manager | Set commission or fixed rate for partner links | 🖥️ | Operations → Partners |
| `/maas/partner/commission/usage/read/v1` | operator | View partner-link usage for commission | 🖥️ | Operations → Partners |
| `/maas/owner-ticket/reply/owner/v1` | operator | Owner operator replies to a Consumer ticket | 🖥️ | Operations → Consumer tickets |
| `/maas/owner-ticket/price-settlement/record/v1` | operator | Record the agreed price or commission for a partner link | 🖥️ | Operations → Consumer tickets |
| `/maas/owner-ticket/close/v1` | operator | Close a Consumer-to-Owner ticket | 🖥️ | Operations → Consumer tickets |
| `/maas/consumer/onboard/v1` | manager | Onboard a new Consumer | 🖥️ | Operations → Onboarding |
| `/maas/consumer/entitlement/grant/v1` | manager | Grant a Consumer the endpoints it bought | 🖥️ | Operations → Onboarding |
| `/maas/consumer/entitlement/revoke/v1` | manager | Revoke a Consumer's endpoints | 🖥️ | Operations → Onboarding |
| `/maas/owner-account/login/v1` | operator | Owner role (manager, developer or operator) signs in | 🖥️ | Operations → Account |
| `/maas/owner-account/logout/v1` | operator | Owner role signs out | 🖥️ | Operations → Account |
| `/maas/owner-account/session/refresh/v1` | operator | Keep the Owner session alive | 🖥️ | Operations → Account |
| `/maas/owner-account/invite/accept/v1` | operator | Accept the invite sent to the Owner role's mail id and set a password | 🖥️ | Operations → Account |
| `/maas/owner-account/password/reset/request/v1` | operator | Request a password reset by mail | 🖥️ | Operations → Account |
| `/maas/owner-account/password/reset/confirm/v1` | operator | Set a new password from the reset mail | 🖥️ | Operations → Account |
| `/maas/owner-account/password/change/v1` | operator | Change own password | 🖥️ | Operations → Account |
| `/maas/owner-role/create/v1` | manager | Create an Owner role (manager, developer, operator) | 🖥️ | Operations → Owner team |
| `/maas/owner-role/read/v1` | manager | View Owner roles | 🖥️ | Operations → Owner team |
| `/maas/owner-role/update/v1` | manager | Edit an Owner role | 🖥️ | Operations → Owner team |
| `/maas/owner-role/deactivate/v1` | manager | Deactivate an Owner role | 🖥️ | Operations → Owner team |
| `/maas/owner-role-mail/list/v1` | manager | List the mail ids that have access to each Owner role | 🖥️ | Operations → Owner team |
| `/maas/owner-role-mail/assign/v1` | manager | Give a mail id access to an Owner role | 🖥️ | Operations → Owner team |
| `/maas/owner-role-mail/remove/v1` | manager | Remove a mail id's access to an Owner role | 🖥️ | Operations → Owner team |
| `/maas/api-key/issue/v1` | developer | Issue an API key to a Consumer | 🖥️ | Operations → Developer |
| `/maas/api-key/rotate/v1` | developer | Rotate a Consumer's API key | 🖥️ | Operations → Developer |
| `/maas/api-key/revoke/v1` | developer | Revoke a Consumer's API key | 🖥️ | Operations → Developer |
| `/maas/endpoint-version/publish/v1` | developer | Publish a new version of an endpoint | 🖥️ | Operations → Developer |
| `/maas/endpoint-version/retire/v1` | developer | Retire an old endpoint version | 🖥️ | Operations → Developer |
| `/maas/endpoint/opt-in/request/read/v1` | operator | View opt-in requests from Consumers | 🖥️ | Operations → Onboarding |
| `/maas/audit/owner-log/read/v1` | manager | View the Owner-side audit log | 🖥️ | Operations → Audit and impact |
| `/maas/impact/baseline/method/define/v1` | manager | Define how the without-AI baseline is estimated | 🖥️ | Operations → Audit and impact |

### Consumer features

#### MaaS · Management: 25 built, 59 in the interface needing the backend

| Endpoint | Who | Feature | Status | Where |
|---|---|---|---|---|
| `/maas/root-account/read/v1` | root | View company account details | ✅ | own screen |
| `/maas/root-account/settings/read/v1` | root | View overall settings | ✅ | own screen |
| `/maas/root-account/settings/update/v1` | root | Change overall settings (root only) | ✅ | own screen |
| `/maas/role/create/v1` | root | Create an internal company role | ✅ | own screen |
| `/maas/role/read/v1` | root | View internal roles | ✅ | own screen |
| `/maas/role/update/v1` | root | Edit an internal role | ✅ | own screen |
| `/maas/role/deactivate/v1` | root | Deactivate an internal role | ✅ | own screen |
| `/maas/role/permission/read/v1` | root | View which endpoints a role may trigger | ✅ | own screen |
| `/maas/role/permission/assign/v1` | root | Grant a role access to a specific endpoint (least privilege) | ✅ | own screen |
| `/maas/role/permission/revoke/v1` | root | Remove a role's access to an endpoint | ✅ | own screen |
| `/maas/notification/root-mail/log/read/v1` | root | View the log of mails sent to the root | ✅ | own screen |
| `/maas/user/staff/list/v1` | root | List internal company users | ✅ | own screen |
| `/maas/user/customer/list/v1` | root | List registered Customers | 🖥️ | Data and audit |
| `/maas/user/customer/read/v1` | staff | View one Customer's account | 🖥️ | Data and audit |
| `/maas/database/record/read/v1` | staff | Read a tenant-scoped record | 🖥️ | Data and audit |
| `/maas/database/record/write/v1` | staff | Write a tenant-scoped record | 🖥️ | Data and audit |
| `/maas/database/export/v1` | root | Export tenant data | 🖥️ | Data and audit |
| `/maas/endpoint/purchased/list/v1` | root | List the endpoints the Consumer has bought from the Owner | 🖥️ | Services and endpoints |
| `/maas/endpoint/customer/enable/v1` | root | Enable a purchased endpoint for Customers | 🖥️ | Services and endpoints |
| `/maas/endpoint/customer/disable/v1` | root | Disable an endpoint for Customers | 🖥️ | Services and endpoints |
| `/maas/interface/template/create/v1` | root | Create the Customer-platform template | ✅ | own screen |
| `/maas/interface/template/read/v1` | root | View the template | ✅ | own screen |
| `/maas/interface/template/update/v1` | root | Edit layout, branding and sections | ✅ | own screen |
| `/maas/interface/template/role-view/update/v1` | root | Set how company roles see their own views | ✅ | own screen |
| `/maas/interface/template/preview/v1` | root | Preview before publishing | ✅ | own screen |
| `/maas/interface/template/publish/v1` | root | Publish the template to Customers | ✅ | own screen |
| `/maas/partner/link/list/v1` | root | List partner links | 🖥️ | Partners |
| `/maas/partner/link/enable/v1` | root | Enable a settled partner link on the Consumer side | 🖥️ | Partners |
| `/maas/partner/link/disable/v1` | root | Disable a partner link | 🖥️ | Partners |
| `/maas/partner/link/customer-access/enable/v1` | root | Open a partner's endpoints to own Customers | 🖥️ | Partners |
| `/maas/partner/link/customer-access/disable/v1` | root | Close a partner's endpoints to own Customers | 🖥️ | Partners |
| `/maas/owner-ticket/create/general/v1` | staff | Raise a ticket with the Owner (platform issue, plan or endpoint question) | 🖥️ | Owner tickets |
| `/maas/owner-ticket/create/partner-link/v1` | root | Request a partner link | 🖥️ | Owner tickets |
| `/maas/owner-ticket/read/v1` | staff | View own Owner tickets | 🖥️ | Owner tickets |
| `/maas/owner-ticket/reply/consumer/v1` | staff | Reply to the Owner in a ticket | 🖥️ | Owner tickets |
| `/maas/analytics/dashboard/read/v1` | root | View summary dashboard across opted-in services | ✅ | own screen |
| `/maas/analytics/usage/read/v1` | root | View endpoint usage | ✅ | own screen |
| `/maas/billing/usage/read/v1` | root | View charges per endpoint and per usage | ✅ | own screen |
| `/maas/billing/invoice/read/v1` | root | View invoices | ✅ | own screen |
| `/maas/fraud/account/flag/read/v1` | staff | View flagged accounts | 🖥️ | Data and audit |
| `/maas/fraud/threshold/update/v1` | root | Set fraud thresholds | 🖥️ | Data and audit |
| `/maas/fraud/review-queue/read/v1` | staff | View the human review queue | 🖥️ | Data and audit |
| `/maas/fraud/review-queue/decide/v1` | staff | Decide a flagged case | 🖥️ | Data and audit |
| `/maas/locale/language/set/v1` | root | Set supported languages for the Consumer | 🖥️ | Settings |
| `/maas/locale/region/set/v1` | root | Set local or global operation and regions | 🖥️ | Settings |
| `/maas/locale/currency/set/v1` | root | Set currencies | 🖥️ | Settings |
| `/maas/interaction/mode/settings/update/v1` | root | Enable text-to-text, text-to-speech, speech-to-text, speech-to-speech | 🖥️ | Settings |
| `/maas/location/store/create/v1` | root | Add a store location | 🖥️ | Stores and locations |
| `/maas/location/store/read/v1` | staff | View store locations | 🖥️ | Stores and locations |
| `/maas/location/store/update/v1` | root | Edit a store location | 🖥️ | Stores and locations |
| `/maas/location/store/deactivate/v1` | root | Deactivate a store location | 🖥️ | Stores and locations |
| `/maas/impact/ledger/read/v1` | root | View the impact ledger across services | 🖥️ | Impact |
| `/maas/impact/baseline/read/v1` | root | View recorded baselines | 🖥️ | Impact |
| `/maas/impact/report/net/read/v1` | root | View the net impact report | 🖥️ | Impact |
| `/maas/impact/ai-footprint/read/v1` | root | View the energy cost of the AI used | 🖥️ | Impact |
| `/maas/impact/source-confidence/read/v1` | root | View data source and confidence for each figure | 🖥️ | Impact |
| `/maas/impact/report/export/v1` | root | Export impact report for ESG reporting | 🖥️ | Impact |
| `/maas/root-account/login/v1` | root | Root signs in | 🖥️ | Account and sign-in |
| `/maas/root-account/logout/v1` | root | Root signs out | 🖥️ | Account and sign-in |
| `/maas/root-account/session/refresh/v1` | root | Keep the root session alive | 🖥️ | Account and sign-in |
| `/maas/root-account/password/reset/request/v1` | root | Request a root password reset by mail | 🖥️ | Account and sign-in |
| `/maas/root-account/password/reset/confirm/v1` | root | Set a new root password from the reset mail | 🖥️ | Account and sign-in |
| `/maas/root-account/password/change/v1` | root | Change the root password | 🖥️ | Account and sign-in |
| `/maas/root-account/mail/update/v1` | root | Change the root contact mail id | 🖥️ | Account and sign-in |
| `/maas/staff-account/invite/accept/v1` | staff | Accept the invite sent to the role's mail id and set a password (first sign-in) | 🖥️ | Account and sign-in |
| `/maas/staff-account/login/v1` | staff | Internal role signs in | 🖥️ | Account and sign-in |
| `/maas/staff-account/logout/v1` | staff | Internal role signs out | 🖥️ | Account and sign-in |
| `/maas/staff-account/session/refresh/v1` | staff | Keep the session alive | 🖥️ | Account and sign-in |
| `/maas/staff-account/password/reset/request/v1` | staff | Request a password reset by mail | 🖥️ | Account and sign-in |
| `/maas/staff-account/password/reset/confirm/v1` | staff | Set a new password from the reset mail | 🖥️ | Account and sign-in |
| `/maas/staff-account/password/change/v1` | staff | Change own password | 🖥️ | Account and sign-in |
| `/maas/role-mail/list/v1` | root | List the mail ids that have access to each role | ✅ | own screen |
| `/maas/role-mail/assign/v1` | root | Give a mail id access to a role | ✅ | own screen |
| `/maas/role-mail/remove/v1` | root | Remove a mail id's access to a role | ✅ | own screen |
| `/maas/api-key/list/v1` | root | View own API keys | 🖥️ | Services and endpoints |
| `/maas/endpoint-version/read/v1` | root | See endpoint versions available to the Consumer | 🖥️ | Services and endpoints |
| `/maas/service/opt-in/request/v1` | root | Request to opt into a service (maas is added automatically) | 🖥️ | Services and endpoints |
| `/maas/endpoint/opt-in/request/v1` | root | Request to opt into a single endpoint | 🖥️ | Services and endpoints |
| `/maas/audit/log/read/v1` | root | View the Consumer's audit log | 🖥️ | Data and audit |
| `/maas/audit/log/export/v1` | root | Export the Consumer's audit log | 🖥️ | Data and audit |
| `/maas/service-identity/permission/read/v1` | root | View what AI and system steps may do | 🖥️ | Services and endpoints |
| `/maas/service-identity/permission/assign/v1` | root | Limit an AI or system step to specific endpoints | 🖥️ | Services and endpoints |
| `/maas/partner/call/log/read/v1` | root | View calls relayed to and from partners | 🖥️ | Partners |
| `/maas/impact/baseline/method/read/v1` | root | View the baseline method behind a figure | 🖥️ | Impact |

#### PaaS · Product: 10 built, 39 in the interface needing the backend

| Endpoint | Who | Feature | Status | Where |
|---|---|---|---|---|
| `/paas/catalog/product/create/v1` | staff | List a new product | ✅ | own screen |
| `/paas/catalog/product/read/v1` | staff | View products (staff list) | ✅ | own screen |
| `/paas/catalog/product/update/v1` | staff | Edit a product | ✅ | own screen |
| `/paas/catalog/product/archive/v1` | staff | Remove a product from sale | ✅ | own screen |
| `/paas/catalog/category/create/v1` | staff | Create a category | 🖥️ | Products and stock |
| `/paas/catalog/category/update/v1` | staff | Edit a category | 🖥️ | Products and stock |
| `/paas/order/read/staff/v1` | staff | View orders | ✅ | own screen |
| `/paas/order/status/update/v1` | staff | Update order status | ✅ | own screen |
| `/paas/offline-sale/record/v1` | staff | Record an in-person sale in the same order record | 🖥️ | Orders |
| `/paas/inventory/stock/read/v1` | staff | View stock | ✅ | own screen |
| `/paas/inventory/stock/update/v1` | staff | Update stock count | ✅ | own screen |
| `/paas/inventory/stock/adjust/v1` | staff | Adjust stock with a reason (damage, loss, correction) | ✅ | own screen |
| `/paas/lifecycle/record/read/v1` | staff | View an item's lifecycle | 🖥️ | Products and stock |
| `/paas/bid/rules/ai-limits/set/v1` | root | Set the limits the AI bot may negotiate within | 🖥️ | Bidding |
| `/paas/bid/ai/decision/accept/v1` | staff | Consumer accepts the finalized deal | 🖥️ | Bidding |
| `/paas/bid/ai/decision/reject/v1` | staff | Consumer rejects the finalized deal | 🖥️ | Bidding |
| `/paas/bid/human/offer/respond/v1` | staff | Consumer responds to a bid | 🖥️ | Bidding |
| `/paas/bid/human/accept/v1` | staff | Accept a human bid | 🖥️ | Bidding |
| `/paas/bid/human/reject/v1` | staff | Reject a human bid | 🖥️ | Bidding |
| `/paas/bid/rules/price-limits/set/v1` | root | Set bid floors and ceilings | 🖥️ | Bidding |
| `/paas/bid/rules/window/set/v1` | root | Set the auction window | 🖥️ | Bidding |
| `/paas/bid/rules/seller-eligibility/set/v1` | root | Set which sellers may bid | 🖥️ | Bidding |
| `/paas/bid/guardrail/review/decide/v1` | staff | Decide a flagged high-value bid | 🖥️ | Bidding |
| `/paas/assistant/config/update/v1` | root | Set assistant scope, tone and enabled modes | 🖥️ | Insights |
| `/paas/forecast/demand/read/v1` | staff | View forecasts | ✅ | own screen |
| `/paas/forecast/reorder/approve/v1` | staff | Approve a reorder suggestion | 🖥️ | Demand forecast |
| `/paas/pricing/dynamic/rules/set/v1` | root | Set dynamic pricing rules | 🖥️ | Pricing and promotions |
| `/paas/pricing/dynamic/apply/v1` | staff | Apply a suggested price | 🖥️ | Pricing and promotions |
| `/paas/stock-rebalance/proposal/accept/v1` | staff | Accept a transfer proposal | 🖥️ | Products and stock |
| `/paas/stock-rebalance/proposal/reject/v1` | staff | Reject a transfer proposal | 🖥️ | Products and stock |
| `/paas/seller-trust/score/read/v1` | staff | View a seller's trust score | 🖥️ | Insights |
| `/paas/environment/origin/submit/v1` | staff | Submit how a product is made (materials, process) | 🖥️ | Products and stock |
| `/paas/green-credits/rules/set/v1` | root | Set how credits are earned and redeemed | 🖥️ | Pricing and promotions |
| `/paas/personalization/limits/set/v1` | root | Set limits on personalization | 🖥️ | Pricing and promotions |
| `/paas/insights/behavior/read/v1` | staff (AI) | See why Customers buy, return or leave | 🖥️ | Insights |
| `/paas/insights/feedback/sentiment/read/v1` | staff (AI) | See common issues from reviews | 🖥️ | Insights |
| `/paas/fraud/order/flag/read/v1` | staff | View flagged orders | 🖥️ | Insights |
| `/paas/fraud/review/decide/v1` | staff | Decide a flagged order | 🖥️ | Insights |
| `/paas/fraud/threshold/update/v1` | root | Set order-fraud thresholds | 🖥️ | Insights |
| `/paas/basket/bundle/create/v1` | staff | Create a bundle | 🖥️ | Pricing and promotions |
| `/paas/segment/read/v1` | staff | View segments | 🖥️ | Pricing and promotions |
| `/paas/segment/offer/send/v1` | staff | Send an offer to a segment | 🖥️ | Pricing and promotions |
| `/paas/pickup/handover/code/verify/v1` | staff | Staff verify the Customer's code | 🖥️ | Orders |
| `/paas/pickup/handover/mark-collected/v1` | staff | Staff mark an order collected | 🖥️ | Orders |
| `/paas/parts/listing/create/v1` | staff | List salvaged parts for sale | 🖥️ | Products and stock |
| `/paas/analytics/sales/read/v1` | staff | View sales analytics | 🖥️ | Insights |
| `/paas/impact/report/read/v1` | root | View Product-service impact | 🖥️ | Insights |
| `/paas/promotion/coupon/create/v1` | staff | Create a coupon or discount | 🖥️ | Pricing and promotions |
| `/paas/promotion/coupon/deactivate/v1` | staff | Deactivate a coupon | 🖥️ | Pricing and promotions |

#### TaaS · Transport: 15 built, 12 in the interface needing the backend

| Endpoint | Who | Feature | Status | Where |
|---|---|---|---|---|
| `/taas/delivery/rules/set/v1` | root | Set delivery options and rules | ✅ | own screen |
| `/taas/shipment/create/v1` | staff | Create a shipment for a sold item | ✅ | own screen |
| `/taas/shipment/read/staff/v1` | staff | View shipments | ✅ | own screen |
| `/taas/shipment/status/update/v1` | staff | Update shipment status | ✅ | own screen |
| `/taas/shipment/cancel/v1` | staff | Cancel a shipment | ✅ | own screen |
| `/taas/delivery/pricing/dynamic/apply/v1` | staff | Apply a suggested delivery price | 🖥️ | Delivery rules |
| `/taas/route/green/select/v1` | staff | Choose the recommended green option | 🖥️ | Delivery rules |
| `/taas/reverse/route/resale/assign/v1` | staff | Route to resale | ✅ | own screen |
| `/taas/reverse/route/refurbish/assign/v1` | staff | Route to refurbishment | ✅ | own screen |
| `/taas/reverse/route/donate/assign/v1` | staff | Route to donation | ✅ | own screen |
| `/taas/reverse/route/parts/assign/v1` | staff | Route to parts harvesting | ✅ | own screen |
| `/taas/reverse/route/recycle/assign/v1` | staff | Route to recycling | ✅ | own screen |
| `/taas/reverse/pickup/schedule/v1` | staff | Schedule the pickup | ✅ | own screen |
| `/taas/reverse/dropoff/store/leg/assign/v1` | staff | Plan the leg from a store drop-off | 🖥️ | Return routes |
| `/taas/pickup/store-leg/assign/v1` | staff | Plan the leg for store pickup instead of delivery | 🖥️ | Return routes |
| `/taas/transfer/stock/create/v1` | staff | Create an inter-seller or inter-location transfer | 🖥️ | Shipments |
| `/taas/transfer/stock/status/update/v1` | staff | Update transfer status | 🖥️ | Shipments |
| `/taas/transfer/stock/receive/v1` | staff | Confirm transfer received | 🖥️ | Shipments |
| `/taas/refurbisher/shipment/create/v1` | staff | Ship an item to a refurbisher | 🖥️ | Shipments |
| `/taas/partner/transport/enable/v1` | root | Use a partner's transport service | 🖥️ | Delivery rules |
| `/taas/partner/transport/offer/v1` | root | Offer own transport to partner Consumers | 🖥️ | Delivery rules |
| `/taas/assistant/config/update/v1` | root | Set delivery-assistant scope and modes | 🖥️ | Delivery rules |
| `/taas/fraud/review/decide/v1` | staff | Decide a flagged delivery case | 🖥️ | Insights |
| `/taas/locale/service-area/set/v1` | root | Set local or global delivery area | ✅ | own screen |
| `/taas/insights/delivery/read/v1` | staff (AI) | See delivery delays and complaints patterns | ✅ | own screen |
| `/taas/analytics/delivery/read/v1` | staff | View delivery analytics | ✅ | own screen |
| `/taas/impact/report/read/v1` | root | View Transport-service impact | ✅ | own screen |

#### SaaS · Support: 9 built, 24 in the interface needing the backend

| Endpoint | Who | Feature | Status | Where |
|---|---|---|---|---|
| `/saas/ticket/read/staff/v1` | staff | View tickets | ✅ | own screen |
| `/saas/ticket/reply/staff/v1` | staff | Staff replies | ✅ | own screen |
| `/saas/ticket/assign/v1` | staff | Assign a ticket | 🖥️ | Tickets |
| `/saas/ticket/status/update/v1` | staff | Update ticket status | ✅ | own screen |
| `/saas/ticket/escalate/v1` | staff | Escalate a ticket | 🖥️ | Tickets |
| `/saas/ticket/close/v1` | staff | Close a ticket | ✅ | own screen |
| `/saas/return/policy/set/v1` | root | Set return rules | ✅ | own screen |
| `/saas/return/request/read/v1` | staff | View return requests | ✅ | own screen |
| `/saas/return/request/approve/v1` | staff | Approve a return | ✅ | own screen |
| `/saas/return/request/reject/v1` | staff | Reject a return | ✅ | own screen |
| `/saas/return/refund/issue/v1` | staff | Issue a refund | ✅ | own screen |
| `/saas/repair/policy/set/v1` | root | Set repair rules | 🖥️ | Repairs and recycling |
| `/saas/repair/status/update/v1` | staff | Update repair progress | 🖥️ | Repairs and recycling |
| `/saas/grading/threshold/set/v1` | root | Set grade and value thresholds | 🖥️ | Returns and refunds |
| `/saas/grading/result/override/v1` | staff | Staff override a grade | 🖥️ | Returns and refunds |
| `/saas/trade-in/process/complete/v1` | staff | Complete the trade-in | 🖥️ | Repairs and recycling |
| `/saas/recycling/handover/record/v1` | staff | Record handover to a recycler | 🖥️ | Repairs and recycling |
| `/saas/refurbisher/assign/v1` | staff | Assign the work | 🖥️ | Repairs and recycling |
| `/saas/dispute/respond/v1` | staff | Respond to a dispute | 🖥️ | Tickets |
| `/saas/dispute/resolve/v1` | staff | Resolve a dispute | 🖥️ | Tickets |
| `/saas/assistant/config/update/v1` | root | Set support-assistant scope and modes | 🖥️ | Tickets |
| `/saas/fraud/return/flag/read/v1` | staff | View flagged returns | 🖥️ | Returns and refunds |
| `/saas/fraud/review/decide/v1` | staff | Decide a flagged return | 🖥️ | Returns and refunds |
| `/saas/scorecard/consumer/read/v1` | root | See the Consumer's circularity scorecard | 🖥️ | Tickets |
| `/saas/insights/ticket-sentiment/read/v1` | staff (AI) | See common ticket issues and sentiment | 🖥️ | Tickets |
| `/saas/analytics/support/read/v1` | staff | View support analytics | 🖥️ | Tickets |
| `/saas/dropoff/store/receive/code-verify/v1` | staff | Staff verify the drop-off code | 🖥️ | Returns and refunds |
| `/saas/dropoff/store/receive/mark-received/v1` | staff | Staff mark the item received | 🖥️ | Returns and refunds |
| `/saas/locale/policy/region/set/v1` | root | Set region-specific return and repair policy | 🖥️ | Tickets |
| `/saas/partner/support/enable/v1` | root | Use a partner's support service | 🖥️ | Tickets |
| `/saas/impact/report/read/v1` | root | View Support-service impact | 🖥️ | Tickets |
| `/saas/partner/issue/relay/v1` | staff | Pass a Customer's issue to a partner's support, while the Customer stays with their own Consumer | 🖥️ | Tickets |
| `/saas/partner/issue/status/read/v1` | staff | Track the issue passed to the partner | 🖥️ | Tickets |

### Left for the backend integration

- [ ] Write a real handler for every 🖥️ feature above, then give the busiest ones a screen of their own
- [ ] Real sign-in with tokens. The email header is trusted as sent today and can be forged (A1)
- [ ] A sign-in path for invited people (D3)
- [ ] Switching deactivated roles back on
- [ ] Sections A to H below

---

## A. Identity and access (do these before the gate counts as a security boundary)

| ID | What is open | Revisit when | Where |
|---|---|---|---|
| A1 | **No real sign-in.** The gate names the consumer by an `X-Tenant-Id` header, so anyone can claim any consumer. Needs real sessions for the four account types, then the gate must read the actor and tenant from the session. | `customer-account/*`, `root-account/login…`, `staff-account/*`, `owner-account/*` (login, logout, session/refresh, password/*, invite/accept, mail/verify) | `cloud_run/gate.py` (`_check`), `ACCOUNTS` in `cloud_sql/services/maas/service.py` (demo hashes) |
| A2 | ✅ **Done 9 Oct 2026.** The gate checks the caller's role permissions (403 `role_not_allowed`), and the root sets them on Roles and Team. Was: **second gate missing: role permission.** A call should also need the root to have allowed the endpoint for the caller's internal role (least privilege, nothing implied). No `RolePermission` records exist. | `role/*`, `role/permission/read\|assign\|revoke`, `role-mail/*` | gate step to add after "purchased" |
| A3 | **Second gate missing: customer enablement.** Customer endpoints need the root to have enabled them for Customers. No `CustomerEnablement` records exist. | `endpoint/customer/enable\|disable`, `endpoint/purchased/list` | gate step to add |
| A4 | **AI and system steps are not limited.** `ServiceIdentityPermission` is not modelled, so AI and System actors are not restricted to specific endpoints. | `service-identity/permission/read\|assign` | gate |
| A5 | **Partner-link check missing.** A consumer opted into a partner endpoint can call it with no link. Needs the link enabled in `maas` and in the service. | `partner/link/*`, `partner/call/relay`, `owner-ticket/create/partner-link`, `taas/partner/*`, `saas/partner/*`, `paas/bid/multi-seller/offer/submit`, `paas/stock-rebalance/proposal/generate`, `saas/refurbisher/*` | gate; the "Needs partner link" label in the Owner UI is only a label |
| A6 | **Wrong-actor check missing.** The gate does not check the caller is the endpoint's actor (for example a Customer calling a Consumer-root endpoint). Follows from A1 to A3. | all | gate |
| A7 | **Tenant isolation on queries and records.** Handlers must scope every query to the tenant, and a Customer account to one Consumer. Nothing to test until handlers exist. | `database/record/*`, every handler | handlers |
| A8 | **Whitelabel.** Customers must never see Owner details. Check each Customer-facing response when its handler is built. | all `Customer` endpoints | handlers |

## B. Opt-in, entitlements and onboarding

| ID | What is open | Revisit when | Where |
|---|---|---|---|
| B1 | **Opt-in requests are not a workflow.** The Owner switches consumers on directly. Consumers should request, and the Owner approve. | `service/opt-in/request`, `endpoint/opt-in/request`, `endpoint/opt-in/request/read` | `set_endpoint_enabled`, `set_service_enabled` in `endpoints.py` |
| B2 | **Entitlement grant and revoke** exist only as the Owner console toggles, not as the endpoints themselves. | `consumer/entitlement/grant\|revoke`, `consumer/onboard`, `root-account/provision` | Owner router |
| B3 | **Service opt-in rules to confirm.** Opting into a service opts in all its consumer-buyable endpoints plus all of MaaS. MaaS cannot be switched off while another service is in use. Owner-side endpoints are never bought by a consumer. Confirm this matches "base endpoints" and "no tiers". | any change to opt-in rules | `endpoints.py` |
| B4 | **Seeded demo opt-ins.** t-001 and t-002 start with all four services, t-003 with MaaS, PaaS and TaaS minus demand forecast read. Replace with real onboarding data. | `consumer/onboard` | `ENDPOINT_ENTITLEMENTS` in `endpoints.py` |
| B5 | **Consumer console features** (workspace, product catalog, shipment tracking, demand forecast) each follow one catalog endpoint. Revisit if the console grows. | consumer console changes | `FEATURE_ENDPOINTS` in `cloud_sql/users/consumer/service.py` |
| B6 | **API keys.** Not issued or checked anywhere. | `api-key/issue\|rotate\|revoke\|list` | gate (when keys are the credential) |
| B7 | **Endpoint versions.** Publish and retire do nothing, and the gate matches the path exactly. | `endpoint-version/publish\|retire\|read` | gate, registry |

## C. Rate limits, pricing and metering

| ID | What is open | Revisit when | Where |
|---|---|---|---|
| C1 | **Rate-limit counts are per process.** With more than one Cloud Run instance each keeps its own count, so the limit is per instance. Needs a shared store (for example Redis). Resets on restart. | before more than one instance | `_window` in `cloud_run/gate.py` |
| C2 | **Usage is sample data plus live counts.** Real usage should come from the audit log. Live counts are in memory. | `analytics/usage/read`, `billing/usage/read`, `billing/invoice/read` | `LIVE_CALLS`, `get_endpoint_usage` in `bigquery/services/maas/service.py` |
| C3 | **Default prices and limits are placeholders.** $0.10 a month and $0.20 per 1,000 calls, intelligence $0.50 and $2.00, rate limit 60 a minute. Confirm or replace. | pricing decision | `DEFAULT_PRICES`, `DEFAULT_RATE_LIMIT` in `endpoints.py` |
| C4 | **Partner pricing.** Commission or fixed rate is settled in an Owner ticket and applied to partner links. Not connected to endpoint prices. | `partner/commission/policy/set`, `partner/commission/usage/read`, `owner-ticket/price-settlement/record`, `partner/link/approve` | none yet |
| C5 | **Billing figures changed.** Revenue and cost now come from endpoint prices and usage (t-001 about $768 a month on the sample). The old 11-API meter no longer bills. Analytics shows revenue by service, not by API. | when real usage lands | `_endpoint_rows`, `get_analytics` in `cloud_run/users/owner/router.py` |
| C6 | ~~**Health card still reads the old 11-API list**~~ **Done 9 Oct:** health is now worked out per endpoint from the live call log (`cloud_run/health.py`: working / slow / failing / not built). The card shows "X of Y built endpoints working", the not-built count and the 24 h success rate, and Monitor has a Status column for each endpoint. | done | `get_overview`, `bigquery/services/maas/service.py`, `API_CATALOG` in `cloud_sql/services/maas/service.py` |
| C7 | **Limits are not bulk-editable.** Settings are one endpoint at a time. | if the Owner asks | Owner UI |

## D. Persistence and audit

| ID | What is open | Revisit when | Where |
|---|---|---|---|
| D1 | **Everything is in memory** (opt-ins, settings, audit log, queries, tickets). Needs real tables: Consumer, EndpointRegistry (seeded from the CSV), Entitlement, EndpointSetting, RolePermission, CustomerEnablement, PartnerLink, AuditLog. | persistence phase | `cloud_sql/services/maas/endpoints.py`, `service.py` |
| D2 | **Audit log is a 2,000-entry buffer** with no page. Should be stored, readable and exportable, and written by the gate for every call (done) and by handlers for changes. | `audit/log/write\|read\|export`, `audit/owner-log/read` | `AUDIT_LOG` in `endpoints.py`; route `/api/v1/owner/consumers/{id}/audit` |
| D3 | **Mail to the root** for every internal-role event, and invites on role-mail assignment, are not built. | `notification/root-mail/*`, `role-mail/invite/send`, `owner-role-mail/invite/send`, `root-account/mail/update` | none yet |

## E. Endpoint definitions to confirm (drafts I wrote, the catalog has no data for them)

| ID | What is open | Revisit when | Where |
|---|---|---|---|
| E1 | **Parameters are a draft** for all 409 endpoints, written from each endpoint's action. Nothing validates them yet. Confirm per feature when its handler is built. 33 endpoints take none and return data directly. | each feature's handlers | `cloud_sql/services/maas/endpoint_params.py` |
| E2 | **HTTP methods are derived** from the action (read, list, view, find, preview, export, scan = GET; update = PATCH; set = PUT; remove, revoke, delete = DELETE; else POST). Deactivate, archive and cancel are POST. Confirm. | each feature's handlers | `_method` in `endpoints.py` |
| E3 | **Categories** are consumer, customer, partner, intelligence, system. Rule: Owner roles hidden; partner (actor Partner, feature `partner`, or depends on a partner link) wins over intelligence; AI flag wins over actor. Confirm the AI-and-partner cases, for example `paas/stock-rebalance/proposal/generate`. | category review | `_category` in `endpoints.py` |
| E4 | **Owner-side endpoints** (32 in MaaS: Owner manager, operator, developer) are hidden from the consumer page and refused by the gate. They show in the Monitor tab. | Owner roles built | `owner_side` in `endpoints.py` |
| E5 | **Catalog items not used yet:** the `list_item` column (master-list item) and the `version` column beyond the path. | when needed | `endpoint_catalog_v1.csv` |

## F. Behaviour of the feature endpoints (from the implementation prompt)

| ID | What is open | Revisit when |
|---|---|---|
| F1 | **Handlers.** Owner and Consumer features without a real handler now get a preview stand-in (`cloud_run/preview.py`, see the 9 Oct checkpoint); Customer, AI, System and Partner ones still return 501 after the gate. Was: all 409 return 501 after the gate. `IMPLEMENTATION_STATUS.md` (done, stubbed or blocked, per service) does not exist yet. | each phase: maas, paas, taas, saas |
| F2 | **AI endpoints** need a stub model behind an interface first, then guardrails: bid floors and ceilings set by the Consumer, human review queue for high-value or flagged cases, prompt-injection screening, PII redaction, and a plain-language explanation on every AI decision. | every endpoint in the intelligence tab; `bid/*`, `fraud/*`, `explain/decision/read` |
| F3 | **Payment** goes through one provider interface with a stub. No provider hardcoded. | `paas/payment/gateway/process`, `paas/payment/invoice/read` |
| F4 | **Interface template vs personalized display** are separate: `maas/interface/template/*` versus `paas/personalization/display/render` and per-service variants. | `interface/template/*`, `personalization/*` |
| F5 | **Impact reporting.** Entries compare with a baseline, state data source and confidence, count the AI compute footprint, and label figures as estimates. Never call anything "proven". | `impact/*` in all four services |
| F6 | **Customer issues go to the Customer's own Consumer**, even when a partner service was involved. | `saas/partner/issue/relay`, `saas/partner/issue/status/read` |
| F7 | **Tests.** Each endpoint needs an allowed-path test and one for each denied case (not purchased, not enabled, wrong actor, wrong tenant). None are written. | each phase |
| F8 | **Definition of done checks:** a call without entitlement fails; entitlement without root enablement fails; cross-tenant access fails; a `paas`-only consumer gets `maas` and cannot call `taas` or `saas`; a partner call needs the link in `maas` and the service. | end of phase 1 gate work |

## G. Out of scope for now (from the implementation prompt)

- Business accounts with several users (single sign-on per account for now).
- Provider-specific payment integrations.
- Custom data-sharing rules with partners.
- Multi-factor sign-in.

## H. Housekeeping

| ID | What is open | Where |
|---|---|---|
| H1 | The backend is run with `uvicorn --reload`, so every file save resets the in-memory state. | dev setup |
| H2 | **Done 9 Oct, removed:** old `API_CATALOG` pricing fields, `API_USAGE`, `API_HEALTH`, `get_api_usage`, `get_api_health`. | `cloud_sql/services/maas/service.py`, `bigquery/services/maas/service.py` |
| H3 | The Owner UI has no page for the audit log yet. | Owner console |
| H4 | `endpoint_catalog_v1.csv` and `implementation_prompt.md` are untracked in git, and the CSV is also copied to `cloud_sql/services/maas/`. Keep the two copies in step, or keep one. | repo root |

## Verification, 9 Oct 2026 (after the move to plain addresses)
- Addresses: `/<user>/<role>/<service>/<category>/<more>`, no `#` (for example `/owner/manager/maas/monitor/paas`, `/consumer/root/saas/returns`, `/customer/individual/paas/catalog`). Old `#/...` links open the same page at its new address.
- Owner: all 32 owner-side endpoints answer 200 for Manager, Developer and Operator. All 32 are listed under Operations tabs, and all 34 Owner pages open with no errors.
- Consumer: all 200 Root and staff endpoints have a handler. Called as Root: 185 return 200; the other 15 are deliberate business-rule refusals (inactive role, duplicate SKU, return not yet approved). Product update and archive return 200 with real ids, and the AI transport flow (recommend, explain, accept, override) works end to end. Each of the 200 maps to one of the 25 Consumer pages, and Root opens all 25 with no errors. Staff roles see only the pages the Root allows.

## Automatic, AI and partner endpoints added, 9 Oct 2026
The 74 endpoints whose actor is System (50), AI (21) or Partner (3) are not started by a signed-in person, so each now belongs to the side whose data it works on:
- **Owner side (2):** `/maas/owner-role-mail/invite/send/v1` and `/maas/audit/log/write/v1`, the platform's own jobs (`OWNER_RUN` in `cloud_sql/services/maas/endpoints.py`). They appear in Operations, Owner team and Operations, Audit and impact.
- **Consumer side (72):** every other one: stock alerts, lifecycle and passport, forecasts and reorder suggestions, bidding and auctions, pricing and personalization, fraud checks, impact baselines and reports, AI routing and grading, refurbisher matching, translations, and partner offers and bids. Each shows as a feature card on its page (`featureCatalog.js`), labelled AI, Automatic or Partner. Each runs on demand in the preview; in production the automatic and AI ones run on their own when their event happens. The Root can also give them to staff roles.
- Each endpoint carries a `runs` field: person, automatic, ai or partner.
- Result: Owner 34 endpoints and Consumer 272, all answering. The health card shows 306 working and 110 not built yet, the Customer endpoints, which are still out of scope.

## Full verification, 9 Oct 2026
- **Endpoints:** all 34 Owner endpoints answer 200 for Manager, Developer and Operator; consumers are refused. Of the 272 Consumer endpoints, 257 answer 200 to the test calls, and the other 15 are correct business-rule refusals. 110 not built: the Customer endpoints only.
- **Rules (69 scenario checks, all pass):**
  - The Owner opts a consumer in or out of an endpoint or a whole service, and the gate and the consumer's lists follow at once.
  - Owner rate limits (429) and prices apply.
  - The three Owner roles see the same 34 features.
  - The Root creates a role, grants and revokes features (AI ones included; Root-only ones refused), assigns people and sets the pages a role sees. A deactivated role loses everything.
  - Staff cannot manage roles. Unnamed callers, outsiders and Owner emails are refused by the consumer gate.
  - Flows checked: products (create, update, archive, negative price refused), orders (forward only), AI delivery planning (recommend, explain, accept, override with a reason; an unfit vehicle is refused), returns (approve, then route), tickets, billing, dashboard, the Owner audit log and visitor queries.
- **Interface (desktop and 375 px phone):**
  - 33 Owner pages for each of the 3 Owner roles.
  - All 25 Consumer pages for the Root, and the allowed pages for Manager, Seller and Dispatcher.
  - The Customer storefront.
  - 0 errors, 0 sideways scroll, no `#` addresses, every page at its `/<user>/<role>/<service>/<category>` address. 34 Owner and 206 Consumer feature cards shown.
