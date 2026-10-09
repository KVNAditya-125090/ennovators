# AuraCommerce 360: functionalities by user

AuraCommerce 360 is a circular-commerce platform with four services: **MaaS** (Management), **PaaS** (Product), **TaaS** (Transport) and **SaaS** (Support). Three kinds of user work on it:

- **Owner**: runs the platform: onboards consumers, decides which features each one gets and at what price, and watches health, cost and revenue.
- **Consumer**: a company (for example a refurbisher or retailer) that runs its business on the platform. Its **Root** account decides what each internal role (Manager, Seller, Dispatcher, or a custom role) can see and do.
- **Customer**: an individual or business buying from a consumer: shopping, bidding, delivery, returns and support.

Every feature is one endpoint of the catalog (`cloud_sql/services/maas/endpoint_catalog_v1.csv`). This file lists them all, generated from the catalog and the interface's own page mapping on 9 Oct 2026.

## Status legend

- ✅ **Built**: a real handler and its own screen. Works now.
- 🖥️ **In the interface (preview)**: the feature is on its page with a form, and the backend answers through a stand-in that records the action and shows it back. It becomes real when its handler is written; the interface stays as it is.
- ⏳ **Not built yet**: in the catalog, with no handler yet (the Customer portal, still out of scope).

| User | Features | ✅ Built | 🖥️ Preview | ⏳ Not built |
|---|---|---|---|---|
| Owner | 34 | 0 | 34 | 0 |
| Consumer | 272 | 66 | 206 | 0 |
| Customer | 110 | 0 | 0 | 110 |
| **Total** | **416** | **66** | **240** | **110** |

## Addresses

Every page has a plain address: `/<user>/<role>/<service>/<category>/<more>`, for example `/owner/manager/maas/monitor/paas`, `/consumer/root/taas/shipments` or `/customer/individual/paas/catalog`. A Consumer feature can be opened directly: `/consumer/root/maas/services/api-key/list` opens its page and scrolls to it. Addresses for another user or role are moved into the signed-in person's own area.

---

## 1. Owner

**Roles:** Manager, Developer and Operator. All three see and can do the same today; per-role limits come later.

**Sign-in:** one sign-in for everyone; the account decides the portal. Demo: `admin@auracommerce.io`, `developer@auracommerce.io`, `operator@auracommerce.io`.

### Console pages

| Page | Address | What it does |
|---|---|---|
| Dashboard | `/owner/<role>/maas/dashboard/<card>` | Cards: health, budget, consumers, revenue, queries. Health (built endpoints working, failing or slow, not built yet, 24 h success rate), budget, consumers, revenue and open visitor queries. Each card opens its history chart (7 days to 12 months). ✅ |
| Queries | `/owner/<role>/maas/queries/<filter>` | Filters: new, in-conversation, closed. Questions visitors send from the home page; reply by mail or phone and move each one along. ✅ |
| Consumers | `/owner/<role>/maas/consumers/<id>/<tab>` | Tabs: services, tickets, or a service (maas, paas, taas, saas). Every consumer with plan, usage and cost. One consumer: details, services, tickets, and per service each endpoint switched on or off with its rate limit, monthly fee and price per 1,000 calls. Whole services on or off. ✅ |
| Operations | `/owner/<role>/maas/operations/<tab>` | The Owner's own catalog features, listed below. 🖥️ |
| Monitor | `/owner/<role>/maas/monitor/<service>` | Every endpoint on the platform with its live status (working, slow, failing, not built), response time, recent calls and how many consumers use it. ✅ |
| Telemetry | `/owner/<role>/maas/telemetry/<level>` | Levels: errors, warnings. Logs from the Google Cloud services behind the platform. ✅ |

### Operations features

#### Onboarding (5)

Onboard consumers, provision their root account, grant or revoke endpoints and review opt-in requests. Address: `/owner/<role>/maas/operations/onboarding`.

| Feature | Done by | Status | Endpoint |
|---|---|---|---|
| Root account is provisioned when a Consumer is onboarded | Manager | 🖥️ | `POST /maas/root-account/provision/v1` |
| Onboard a new Consumer | Manager | 🖥️ | `POST /maas/consumer/onboard/v1` |
| Grant a Consumer the endpoints it bought | Manager | 🖥️ | `POST /maas/consumer/entitlement/grant/v1` |
| Revoke a Consumer's endpoints | Manager | 🖥️ | `DELETE /maas/consumer/entitlement/revoke/v1` |
| View opt-in requests from Consumers | Operator | 🖥️ | `GET /maas/endpoint/opt-in/request/read/v1` |

#### Consumer tickets (3)

Reply to and close the tickets consumers raise, and record agreed prices. Address: `/owner/<role>/maas/operations/tickets`.

| Feature | Done by | Status | Endpoint |
|---|---|---|---|
| Owner operator replies to a Consumer ticket | Operator | 🖥️ | `POST /maas/owner-ticket/reply/owner/v1` |
| Record the agreed price or commission for a partner link | Operator | 🖥️ | `POST /maas/owner-ticket/price-settlement/record/v1` |
| Close a Consumer-to-Owner ticket | Operator | 🖥️ | `POST /maas/owner-ticket/close/v1` |

#### Partners (3)

Approve brokered partner links, set the commission policy and see partner usage. Address: `/owner/<role>/maas/operations/partners`.

| Feature | Done by | Status | Endpoint |
|---|---|---|---|
| Record a brokered partner link after settlement | Operator | 🖥️ | `POST /maas/partner/link/approve/v1` |
| Set commission or fixed rate for partner links | Manager | 🖥️ | `PUT /maas/partner/commission/policy/set/v1` |
| View partner-link usage for commission | Operator | 🖥️ | `GET /maas/partner/commission/usage/read/v1` |

#### Owner team (8)

Owner roles (manager, developer, operator) and the mail ids that hold them. Address: `/owner/<role>/maas/operations/team`.

| Feature | Done by | Status | Endpoint |
|---|---|---|---|
| Create an Owner role (manager, developer, operator) | Manager | 🖥️ | `POST /maas/owner-role/create/v1` |
| View Owner roles | Manager | 🖥️ | `GET /maas/owner-role/read/v1` |
| Edit an Owner role | Manager | 🖥️ | `PATCH /maas/owner-role/update/v1` |
| Deactivate an Owner role | Manager | 🖥️ | `POST /maas/owner-role/deactivate/v1` |
| List the mail ids that have access to each Owner role | Manager | 🖥️ | `GET /maas/owner-role-mail/list/v1` |
| Give a mail id access to an Owner role | Manager | 🖥️ | `POST /maas/owner-role-mail/assign/v1` |
| Remove a mail id's access to an Owner role | Manager | 🖥️ | `DELETE /maas/owner-role-mail/remove/v1` |
| Send the sign-in invite to the assigned Owner mail id | Automatic | 🖥️ | `POST /maas/owner-role-mail/invite/send/v1` |

#### Developer (5)

API keys for consumers, and endpoint versions. Address: `/owner/<role>/maas/operations/developer`.

| Feature | Done by | Status | Endpoint |
|---|---|---|---|
| Issue an API key to a Consumer | Developer | 🖥️ | `POST /maas/api-key/issue/v1` |
| Rotate a Consumer's API key | Developer | 🖥️ | `POST /maas/api-key/rotate/v1` |
| Revoke a Consumer's API key | Developer | 🖥️ | `DELETE /maas/api-key/revoke/v1` |
| Publish a new version of an endpoint | Developer | 🖥️ | `POST /maas/endpoint-version/publish/v1` |
| Retire an old endpoint version | Developer | 🖥️ | `POST /maas/endpoint-version/retire/v1` |

#### Audit and impact (3)

The Owner-side audit log and how impact baselines are estimated. Address: `/owner/<role>/maas/operations/governance`.

| Feature | Done by | Status | Endpoint |
|---|---|---|---|
| Record every endpoint call (who, what, when) | Automatic | 🖥️ | `POST /maas/audit/log/write/v1` |
| View the Owner-side audit log | Manager | 🖥️ | `GET /maas/audit/owner-log/read/v1` |
| Define how the without-AI baseline is estimated | Manager | 🖥️ | `POST /maas/impact/baseline/method/define/v1` |

#### Account (7)

Sign-in, sessions, invites and passwords for Owner accounts. Address: `/owner/<role>/maas/operations/account`.

| Feature | Done by | Status | Endpoint |
|---|---|---|---|
| Owner role (manager, developer or operator) signs in | Operator | 🖥️ | `POST /maas/owner-account/login/v1` |
| Owner role signs out | Operator | 🖥️ | `POST /maas/owner-account/logout/v1` |
| Keep the Owner session alive | Operator | 🖥️ | `POST /maas/owner-account/session/refresh/v1` |
| Accept the invite sent to the Owner role's mail id and set a password | Operator | 🖥️ | `POST /maas/owner-account/invite/accept/v1` |
| Request a password reset by mail | Operator | 🖥️ | `POST /maas/owner-account/password/reset/request/v1` |
| Set a new password from the reset mail | Operator | 🖥️ | `POST /maas/owner-account/password/reset/confirm/v1` |
| Change own password | Operator | 🖥️ | `POST /maas/owner-account/password/change/v1` |

### What the Owner controls for consumers

- **Opt-in:** which services and endpoints each consumer has. A switched-off endpoint is refused at once and disappears from the consumer's pages.
- **Limits and prices:** rate limit per minute, monthly fee and price per 1,000 calls, per endpoint and per consumer.
- **Audit:** every call each consumer makes, allowed or refused, with who, what, when and how long it took.
- **Platform jobs:** the Owner team invites and the platform audit log run on the Owner side and are never sold to consumers.

---

## 2. Consumer

**Roles:** the **Root** (the company account) and the staff roles the Root creates. Demo workspace GreenCycle Refurbishers: Root `seller@greencycle.com`, Manager `rahul@greencycle.com`, Seller `anika@greencycle.com`, Dispatcher `priya@greencycle.com`.

### How the Root controls each role

1. **What the workspace has:** only the endpoints the Owner opted the workspace into exist for anyone in it.
2. **What a role may do:** on *Roles and Team*, the Root gives each role features (staff, automatic, AI and partner ones) and assigns people by email. Root-only features (roles, billing, settings and similar) cannot be given away.
3. **What a role sees:** on *Customization*, the Root picks the pages each role sees and the page it opens on.
4. **Deactivating a role** takes everything away from its holders at once. The gate enforces all of this, not just the screens.

Demo roles as they start:

| Role | State | Features given | Held by |
|---|---|---|---|
| Manager | Active | 3 | rahul@greencycle.com |
| Seller | Active | 3 | anika@greencycle.com |
| Dispatcher | Active | 10 | priya@greencycle.com |

**Who does it** in the tables below: **Root**, **Staff** (any role the Root allows), **Automatic** (runs by itself when its event happens; in the preview you can run it by hand), **AI** (a model suggests, a person decides), **Partner** (a linked partner company acts; recorded by the consumer for now).

Every page also has **Ctrl+K search** over all pages and features.

### MaaS: Management as a Service (89 features)

#### Overview (3)

Address: `/consumer/<role>/maas/overview`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Root account**: View company account details | Root | ✅ | `GET /maas/root-account/read/v1` |
| **Analytics**: View summary dashboard across opted-in services | Root | ✅ | `GET /maas/analytics/dashboard/read/v1` |
| **Analytics**: View endpoint usage | Root | ✅ | `GET /maas/analytics/usage/read/v1` |

#### Billing and Cost (2)

Address: `/consumer/<role>/maas/billing`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Billing**: View charges per endpoint and per usage | Root | ✅ | `GET /maas/billing/usage/read/v1` |
| **Billing**: View invoices | Root | ✅ | `GET /maas/billing/invoice/read/v1` |

#### Roles and Team (14)

Address: `/consumer/<role>/maas/team`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Role**: Create an internal company role | Root | ✅ | `POST /maas/role/create/v1` |
| **Role**: View internal roles | Root | ✅ | `GET /maas/role/read/v1` |
| **Role**: Edit an internal role | Root | ✅ | `PATCH /maas/role/update/v1` |
| **Role**: Deactivate an internal role | Root | ✅ | `POST /maas/role/deactivate/v1` |
| **Role**: View which endpoints a role may trigger | Root | ✅ | `GET /maas/role/permission/read/v1` |
| **Role**: Grant a role access to a specific endpoint (least privilege) | Root | ✅ | `POST /maas/role/permission/assign/v1` |
| **Role**: Remove a role's access to an endpoint | Root | ✅ | `DELETE /maas/role/permission/revoke/v1` |
| **Notification**: Send the root a mail for any internal role event | Automatic | 🖥️ | `POST /maas/notification/root-mail/send/v1` |
| **Notification**: View the log of mails sent to the root | Root | ✅ | `GET /maas/notification/root-mail/log/read/v1` |
| **User**: List internal company users | Root | ✅ | `GET /maas/user/staff/list/v1` |
| **Role mail**: List the mail ids that have access to each role | Root | ✅ | `GET /maas/role-mail/list/v1` |
| **Role mail**: Give a mail id access to a role | Root | ✅ | `POST /maas/role-mail/assign/v1` |
| **Role mail**: Remove a mail id's access to a role | Root | ✅ | `DELETE /maas/role-mail/remove/v1` |
| **Role mail**: Send the sign-in invite to the assigned mail id | Automatic | 🖥️ | `POST /maas/role-mail/invite/send/v1` |

#### Customization (6)

Address: `/consumer/<role>/maas/customize`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Interface**: Create the Customer-platform template | Root | ✅ | `POST /maas/interface/template/create/v1` |
| **Interface**: View the template | Root | ✅ | `GET /maas/interface/template/read/v1` |
| **Interface**: Edit layout, branding and sections | Root | ✅ | `PATCH /maas/interface/template/update/v1` |
| **Interface**: Set how company roles see their own views | Root | ✅ | `PATCH /maas/interface/template/role-view/update/v1` |
| **Interface**: Preview before publishing | Root | ✅ | `GET /maas/interface/template/preview/v1` |
| **Interface**: Publish the template to Customers | Root | ✅ | `POST /maas/interface/template/publish/v1` |

#### Services and endpoints (9)

Address: `/consumer/<role>/maas/services`. What your workspace has bought, what your customers can use, opt-in requests, API keys and service identities.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Endpoint**: List the endpoints the Consumer has bought from the Owner | Root | 🖥️ | `GET /maas/endpoint/purchased/list/v1` |
| **Endpoint**: Enable a purchased endpoint for Customers | Root | 🖥️ | `POST /maas/endpoint/customer/enable/v1` |
| **Endpoint**: Disable an endpoint for Customers | Root | 🖥️ | `POST /maas/endpoint/customer/disable/v1` |
| **Endpoint**: Request to opt into a single endpoint | Root | 🖥️ | `POST /maas/endpoint/opt-in/request/v1` |
| **Api key**: View own API keys | Root | 🖥️ | `GET /maas/api-key/list/v1` |
| **Endpoint version**: See endpoint versions available to the Consumer | Root | 🖥️ | `GET /maas/endpoint-version/read/v1` |
| **Service**: Request to opt into a service (maas is added automatically) | Root | 🖥️ | `POST /maas/service/opt-in/request/v1` |
| **Service identity**: View what AI and system steps may do | Root | 🖥️ | `GET /maas/service-identity/permission/read/v1` |
| **Service identity**: Limit an AI or system step to specific endpoints | Root | 🖥️ | `POST /maas/service-identity/permission/assign/v1` |

#### Partners (7)

Address: `/consumer/<role>/maas/partners`. Links with partner consumers, and what your customers may use through them.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Partner**: List partner links | Root | 🖥️ | `GET /maas/partner/link/list/v1` |
| **Partner**: Enable a settled partner link on the Consumer side | Root | 🖥️ | `POST /maas/partner/link/enable/v1` |
| **Partner**: Disable a partner link | Root | 🖥️ | `POST /maas/partner/link/disable/v1` |
| **Partner**: Open a partner's endpoints to own Customers | Root | 🖥️ | `POST /maas/partner/link/customer-access/enable/v1` |
| **Partner**: Close a partner's endpoints to own Customers | Root | 🖥️ | `POST /maas/partner/link/customer-access/disable/v1` |
| **Partner**: Carry a call from one Consumer to a partner through the interlinking API, limited to enabled endpoints | Automatic | 🖥️ | `POST /maas/partner/call/relay/v1` |
| **Partner**: View calls relayed to and from partners | Root | 🖥️ | `GET /maas/partner/call/log/read/v1` |

#### Owner tickets (4)

Address: `/consumer/<role>/maas/owner`. Questions and partner-link requests you raise with the platform owner.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Owner ticket**: Raise a ticket with the Owner (platform issue, plan or endpoint question) | Staff | 🖥️ | `POST /maas/owner-ticket/create/general/v1` |
| **Owner ticket**: Request a partner link | Root | 🖥️ | `POST /maas/owner-ticket/create/partner-link/v1` |
| **Owner ticket**: View own Owner tickets | Staff | 🖥️ | `GET /maas/owner-ticket/read/v1` |
| **Owner ticket**: Reply to the Owner in a ticket | Staff | 🖥️ | `POST /maas/owner-ticket/reply/consumer/v1` |

#### Stores and locations (4)

Address: `/consumer/<role>/maas/locations`. Your stores, for pickups, drop-offs and local delivery.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Location**: Add a store location | Root | 🖥️ | `POST /maas/location/store/create/v1` |
| **Location**: View store locations | Staff | 🖥️ | `GET /maas/location/store/read/v1` |
| **Location**: Edit a store location | Root | 🖥️ | `PATCH /maas/location/store/update/v1` |
| **Location**: Deactivate a store location | Root | 🖥️ | `POST /maas/location/store/deactivate/v1` |

#### Data and audit (12)

Address: `/consumer/<role>/maas/data`. Customers, records, the audit log and fraud review.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **User**: List registered Customers | Root | 🖥️ | `GET /maas/user/customer/list/v1` |
| **User**: View one Customer's account | Staff | 🖥️ | `GET /maas/user/customer/read/v1` |
| **Database**: Read a tenant-scoped record | Staff | 🖥️ | `GET /maas/database/record/read/v1` |
| **Database**: Write a tenant-scoped record | Staff | 🖥️ | `POST /maas/database/record/write/v1` |
| **Database**: Export tenant data | Root | 🖥️ | `GET /maas/database/export/v1` |
| **Fraud**: Flag suspicious sign-ups and account activity | Automatic | 🖥️ | `POST /maas/fraud/account/detect/v1` |
| **Fraud**: View flagged accounts | Staff | 🖥️ | `GET /maas/fraud/account/flag/read/v1` |
| **Fraud**: Set fraud thresholds | Root | 🖥️ | `PATCH /maas/fraud/threshold/update/v1` |
| **Fraud**: View the human review queue | Staff | 🖥️ | `GET /maas/fraud/review-queue/read/v1` |
| **Fraud**: Decide a flagged case | Staff | 🖥️ | `POST /maas/fraud/review-queue/decide/v1` |
| **Audit**: View the Consumer's audit log | Root | 🖥️ | `GET /maas/audit/log/read/v1` |
| **Audit**: Export the Consumer's audit log | Root | 🖥️ | `GET /maas/audit/log/export/v1` |

#### Impact (8)

Address: `/consumer/<role>/maas/impact`. Environmental impact of your workspace, with baselines, sources and confidence.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Impact**: View the impact ledger across services | Root | 🖥️ | `GET /maas/impact/ledger/read/v1` |
| **Impact**: View recorded baselines | Root | 🖥️ | `GET /maas/impact/baseline/read/v1` |
| **Impact**: Generate net impact against baseline | Automatic | 🖥️ | `POST /maas/impact/report/net/generate/v1` |
| **Impact**: View the net impact report | Root | 🖥️ | `GET /maas/impact/report/net/read/v1` |
| **Impact**: View the energy cost of the AI used | Root | 🖥️ | `GET /maas/impact/ai-footprint/read/v1` |
| **Impact**: View data source and confidence for each figure | Root | 🖥️ | `GET /maas/impact/source-confidence/read/v1` |
| **Impact**: Export impact report for ESG reporting | Root | 🖥️ | `GET /maas/impact/report/export/v1` |
| **Impact**: View the baseline method behind a figure | Root | 🖥️ | `GET /maas/impact/baseline/method/read/v1` |

#### Account and sign-in (14)

Address: `/consumer/<role>/maas/account`. Sign-in, sessions, passwords and invites for the root and staff accounts.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Root account**: Root signs in | Root | 🖥️ | `POST /maas/root-account/login/v1` |
| **Root account**: Root signs out | Root | 🖥️ | `POST /maas/root-account/logout/v1` |
| **Root account**: Keep the root session alive | Root | 🖥️ | `POST /maas/root-account/session/refresh/v1` |
| **Root account**: Request a root password reset by mail | Root | 🖥️ | `POST /maas/root-account/password/reset/request/v1` |
| **Root account**: Set a new root password from the reset mail | Root | 🖥️ | `POST /maas/root-account/password/reset/confirm/v1` |
| **Root account**: Change the root password | Root | 🖥️ | `POST /maas/root-account/password/change/v1` |
| **Root account**: Change the root contact mail id | Root | 🖥️ | `PATCH /maas/root-account/mail/update/v1` |
| **Staff account**: Accept the invite sent to the role's mail id and set a password (first sign-in) | Staff | 🖥️ | `POST /maas/staff-account/invite/accept/v1` |
| **Staff account**: Internal role signs in | Staff | 🖥️ | `POST /maas/staff-account/login/v1` |
| **Staff account**: Internal role signs out | Staff | 🖥️ | `POST /maas/staff-account/logout/v1` |
| **Staff account**: Keep the session alive | Staff | 🖥️ | `POST /maas/staff-account/session/refresh/v1` |
| **Staff account**: Request a password reset by mail | Staff | 🖥️ | `POST /maas/staff-account/password/reset/request/v1` |
| **Staff account**: Set a new password from the reset mail | Staff | 🖥️ | `POST /maas/staff-account/password/reset/confirm/v1` |
| **Staff account**: Change own password | Staff | 🖥️ | `POST /maas/staff-account/password/change/v1` |

#### Settings (6)

Address: `/consumer/<role>/maas/settings`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Root account**: View overall settings | Root | ✅ | `GET /maas/root-account/settings/read/v1` |
| **Root account**: Change overall settings (root only) | Root | ✅ | `PATCH /maas/root-account/settings/update/v1` |
| **Locale**: Set supported languages for the Consumer | Root | 🖥️ | `PUT /maas/locale/language/set/v1` |
| **Locale**: Set local or global operation and regions | Root | 🖥️ | `PUT /maas/locale/region/set/v1` |
| **Locale**: Set currencies | Root | 🖥️ | `PUT /maas/locale/currency/set/v1` |
| **Interaction**: Enable text-to-text, text-to-speech, speech-to-text, speech-to-speech | Root | 🖥️ | `PATCH /maas/interaction/mode/settings/update/v1` |

### PaaS: Product as a Service (85 features)

#### Products and stock (21)

Address: `/consumer/<role>/paas/products`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Catalog**: List a new product | Staff | ✅ | `POST /paas/catalog/product/create/v1` |
| **Catalog**: View products (staff list) | Staff | ✅ | `GET /paas/catalog/product/read/v1` |
| **Catalog**: Edit a product | Staff | ✅ | `PATCH /paas/catalog/product/update/v1` |
| **Catalog**: Remove a product from sale | Staff | ✅ | `POST /paas/catalog/product/archive/v1` |
| **Catalog**: Create a category | Staff | 🖥️ | `POST /paas/catalog/category/create/v1` |
| **Catalog**: Edit a category | Staff | 🖥️ | `PATCH /paas/catalog/category/update/v1` |
| **Inventory**: View stock | Staff | ✅ | `GET /paas/inventory/stock/read/v1` |
| **Inventory**: Update stock count | Staff | ✅ | `PATCH /paas/inventory/stock/update/v1` |
| **Inventory**: Adjust stock with a reason (damage, loss, correction) | Staff | ✅ | `POST /paas/inventory/stock/adjust/v1` |
| **Inventory**: Alert staff on low stock | Automatic | 🖥️ | `POST /paas/inventory/low-stock/alert/v1` |
| **Lifecycle**: Create the lifecycle record at intake | Automatic | 🖥️ | `POST /paas/lifecycle/record/create/v1` |
| **Lifecycle**: View an item's lifecycle | Staff | 🖥️ | `GET /paas/lifecycle/record/read/v1` |
| **Lifecycle**: Move an item to its next state | Automatic | 🖥️ | `PATCH /paas/lifecycle/state/update/v1` |
| **Passport**: Generate the digital product passport | Automatic | 🖥️ | `POST /paas/passport/generate/v1` |
| **Passport**: Pass the passport to the next owner on resale | Automatic | 🖥️ | `POST /paas/passport/ownership/transfer/v1` |
| **Stock rebalance**: Accept a transfer proposal | Staff | 🖥️ | `POST /paas/stock-rebalance/proposal/accept/v1` |
| **Stock rebalance**: Reject a transfer proposal | Staff | 🖥️ | `POST /paas/stock-rebalance/proposal/reject/v1` |
| **Environment**: Submit how a product is made (materials, process) | Staff | 🖥️ | `POST /paas/environment/origin/submit/v1` |
| **Environment**: Check origin and manufacturing data | AI | 🖥️ | `POST /paas/environment/origin/verify/v1` |
| **Parts**: List salvaged parts for sale | Staff | 🖥️ | `POST /paas/parts/listing/create/v1` |
| **Locale**: Translate listings | AI | 🖥️ | `POST /paas/locale/listing/translate/v1` |

#### Orders (6)

Address: `/consumer/<role>/paas/orders`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Order**: View orders | Staff | ✅ | `GET /paas/order/read/staff/v1` |
| **Order**: Update order status | Staff | ✅ | `PATCH /paas/order/status/update/v1` |
| **Offline sale**: Record an in-person sale in the same order record | Staff | 🖥️ | `POST /paas/offline-sale/record/v1` |
| **Pickup**: Create a collection code or QR | Automatic | 🖥️ | `POST /paas/pickup/handover/code/generate/v1` |
| **Pickup**: Staff verify the Customer's code | Staff | 🖥️ | `POST /paas/pickup/handover/code/verify/v1` |
| **Pickup**: Staff mark an order collected | Staff | 🖥️ | `POST /paas/pickup/handover/mark-collected/v1` |

#### Demand forecast (5)

Address: `/consumer/<role>/paas/forecast`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Forecast**: Run demand and inventory forecast per SKU and location | Automatic | 🖥️ | `POST /paas/forecast/demand/run/v1` |
| **Forecast**: View forecasts | Staff | ✅ | `GET /paas/forecast/demand/read/v1` |
| **Forecast**: Suggest reorder points and safety stock | AI | 🖥️ | `POST /paas/forecast/reorder/suggest/v1` |
| **Forecast**: Approve a reorder suggestion | Staff | 🖥️ | `POST /paas/forecast/reorder/approve/v1` |
| **Stock rebalance**: Propose moving stock between sellers or locations | AI | 🖥️ | `POST /paas/stock-rebalance/proposal/generate/v1` |

#### Bidding (18)

Address: `/consumer/<role>/paas/bidding`. Rules and guardrails for customer bids, AI decisions and human offers.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Bid**: Set the limits the AI bot may negotiate within | Root | 🖥️ | `PUT /paas/bid/rules/ai-limits/set/v1` |
| **Bid**: Bot sends a counter-offer to the Customer | AI | 🖥️ | `POST /paas/bid/ai/counter-offer/send/v1` |
| **Bid**: Bot hands the finalized deal to the Consumer | AI | 🖥️ | `POST /paas/bid/ai/finalize/handoff/v1` |
| **Bid**: Consumer accepts the finalized deal | Staff | 🖥️ | `POST /paas/bid/ai/decision/accept/v1` |
| **Bid**: Consumer rejects the finalized deal | Staff | 🖥️ | `POST /paas/bid/ai/decision/reject/v1` |
| **Bid**: Consumer responds to a bid | Staff | 🖥️ | `POST /paas/bid/human/offer/respond/v1` |
| **Bid**: Accept a human bid | Staff | 🖥️ | `POST /paas/bid/human/accept/v1` |
| **Bid**: Reject a human bid | Staff | 🖥️ | `POST /paas/bid/human/reject/v1` |
| **Bid**: Match eligible sellers (stock, location, rating, condition) | AI | 🖥️ | `POST /paas/bid/multi-seller/seller-match/v1` |
| **Bid**: A seller submits an offer | Partner | 🖥️ | `POST /paas/bid/multi-seller/offer/submit/v1` |
| **Bid**: Award the best-fit offer | Automatic | 🖥️ | `POST /paas/bid/multi-seller/award/v1` |
| **Bid**: Set bid floors and ceilings | Root | 🖥️ | `PUT /paas/bid/rules/price-limits/set/v1` |
| **Bid**: Set the auction window | Root | 🖥️ | `PUT /paas/bid/rules/window/set/v1` |
| **Bid**: Set which sellers may bid | Root | 🖥️ | `PUT /paas/bid/rules/seller-eligibility/set/v1` |
| **Bid**: Detect collusion or price manipulation | Automatic | 🖥️ | `POST /paas/bid/guardrail/anomaly/detect/v1` |
| **Bid**: Decide a flagged high-value bid | Staff | 🖥️ | `POST /paas/bid/guardrail/review/decide/v1` |
| **Auction**: Open an auction when surplus is forecast | Automatic | 🖥️ | `POST /paas/auction/surplus/open/v1` |
| **Auction**: Close the auction and award | Automatic | 🖥️ | `POST /paas/auction/surplus/close/v1` |

#### Pricing and promotions (19)

Address: `/consumer/<role>/paas/pricing`. Dynamic pricing, coupons, bundles, customer segments, green credits and personalization.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Pricing**: Set dynamic pricing rules | Root | 🖥️ | `PUT /paas/pricing/dynamic/rules/set/v1` |
| **Pricing**: Suggest a price from demand, condition and competition | AI | 🖥️ | `POST /paas/pricing/dynamic/suggest/v1` |
| **Pricing**: Apply a suggested price | Staff | 🖥️ | `POST /paas/pricing/dynamic/apply/v1` |
| **Pricing**: Lower price along remaining shelf or season life | Automatic | 🖥️ | `POST /paas/pricing/shelf-life-decay/apply/v1` |
| **Future value**: Issue the guarantee at purchase | Automatic | 🖥️ | `POST /paas/future-value/guarantee/issue/v1` |
| **Trade in**: Invite a trade-in while value is still high | AI | 🖥️ | `POST /paas/trade-in/nudge/send/v1` |
| **Green credits**: Set how credits are earned and redeemed | Root | 🖥️ | `PUT /paas/green-credits/rules/set/v1` |
| **Green credits**: Award credits | Automatic | 🖥️ | `POST /paas/green-credits/earn/v1` |
| **Personalization**: Set limits on personalization | Root | 🖥️ | `PUT /paas/personalization/limits/set/v1` |
| **Personalization**: Build a per-Customer profile from activity with this Consumer | Automatic | 🖥️ | `POST /paas/personalization/profile/build/v1` |
| **Personalization**: Fill the Consumer's template with data for this Customer | Automatic | 🖥️ | `POST /paas/personalization/display/render/v1` |
| **Basket**: Propose bundles and cross-sell offers | AI | 🖥️ | `POST /paas/basket/bundle/suggest/v1` |
| **Basket**: Create a bundle | Staff | 🖥️ | `POST /paas/basket/bundle/create/v1` |
| **Segment**: Group Customers by behavior and value | Automatic | 🖥️ | `POST /paas/segment/generate/v1` |
| **Segment**: View segments | Staff | 🖥️ | `GET /paas/segment/read/v1` |
| **Segment**: Send an offer to a segment | Staff | 🖥️ | `POST /paas/segment/offer/send/v1` |
| **Locale**: Show prices in the Customer's currency | Automatic | 🖥️ | `POST /paas/locale/price/currency-convert/v1` |
| **Promotion**: Create a coupon or discount | Staff | 🖥️ | `POST /paas/promotion/coupon/create/v1` |
| **Promotion**: Deactivate a coupon | Staff | 🖥️ | `POST /paas/promotion/coupon/deactivate/v1` |

#### Insights (16)

Address: `/consumer/<role>/paas/insights`. Sales, customer behaviour, seller trust, fraud review, impact and the shopping assistant.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Assistant**: Set assistant scope, tone and enabled modes | Root | 🖥️ | `PATCH /paas/assistant/config/update/v1` |
| **Seller trust**: Update a seller's trust score | Automatic | 🖥️ | `PATCH /paas/seller-trust/score/update/v1` |
| **Seller trust**: View a seller's trust score | Staff | 🖥️ | `GET /paas/seller-trust/score/read/v1` |
| **Environment**: Calculate the environmental score (impact, recycling factor) | Automatic | 🖥️ | `POST /paas/environment/score/calculate/v1` |
| **Insights**: See why Customers buy, return or leave | Staff | 🖥️ | `GET /paas/insights/behavior/read/v1` |
| **Insights**: See common issues from reviews | Staff | 🖥️ | `GET /paas/insights/feedback/sentiment/read/v1` |
| **Fraud**: Flag suspicious orders and payments | Automatic | 🖥️ | `POST /paas/fraud/order/detect/v1` |
| **Fraud**: View flagged orders | Staff | 🖥️ | `GET /paas/fraud/order/flag/read/v1` |
| **Fraud**: Decide a flagged order | Staff | 🖥️ | `POST /paas/fraud/review/decide/v1` |
| **Fraud**: Set order-fraud thresholds | Root | 🖥️ | `PATCH /paas/fraud/threshold/update/v1` |
| **Analytics**: View sales analytics | Staff | 🖥️ | `GET /paas/analytics/sales/read/v1` |
| **Impact**: Record what would have happened without the AI (e.g. unsold stock) | Automatic | 🖥️ | `POST /paas/impact/baseline/record/v1` |
| **Impact**: Record the estimated saving from each event | Automatic | 🖥️ | `POST /paas/impact/event/record/v1` |
| **Impact**: View Product-service impact | Root | 🖥️ | `GET /paas/impact/report/read/v1` |
| **Impact**: Generate the Product-service impact report | Automatic | 🖥️ | `POST /paas/impact/report/generate/v1` |
| **Impact**: Estimate extra consumption caused by cheaper bids and easier buying | Automatic | 🖥️ | `POST /paas/impact/rebound/estimate/v1` |

### TaaS: Transport as a Service (49 features)

#### Shipments (20)

Address: `/consumer/<role>/taas/shipments`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Shipment**: Create a shipment for a sold item | Staff | ✅ | `POST /taas/shipment/create/v1` |
| **Shipment**: View shipments | Staff | ✅ | `GET /taas/shipment/read/staff/v1` |
| **Shipment**: Update shipment status | Staff | ✅ | `PATCH /taas/shipment/status/update/v1` |
| **Shipment**: Cancel a shipment | Staff | ✅ | `POST /taas/shipment/cancel/v1` |
| **Tracking**: Notify the Customer of delivery updates | Automatic | 🖥️ | `POST /taas/tracking/notification/send/v1` |
| **Route**: Calculate the shortest path | Automatic | 🖥️ | `POST /taas/route/shortest/calculate/v1` |
| **Route**: Recommend a low-pollution route and transport mode | AI | 🖥️ | `POST /taas/route/green/recommend/v1` |
| **Route**: Explain why this route and mode were recommended | AI | 🖥️ | `POST /taas/route/green/explain/v1` |
| **Route**: Recommend the best route (shortest / fastest / cheapest / greenest) across one or more stops | Staff | ✅ | `POST /taas/route/optimize/recommend/v1` |
| **Vehicle**: Recommend the vehicle type for a shipment from its load and distance | Staff | ✅ | `POST /taas/vehicle/recommend/v1` |
| **Delivery**: Predict the delivery date and time | Staff | ✅ | `POST /taas/delivery/eta/predict/v1` |
| **Delivery**: Recommend delivery slots with their on-time likelihood | Staff | ✅ | `POST /taas/delivery/slot/recommend/v1` |
| **Explain**: Read the plain-language reason for a route / vehicle / slot or delivery-time recommendation | Staff | ✅ | `GET /taas/explain/decision/read/v1` |
| **Recommendation**: Accept an AI transport recommendation for a shipment | Staff | ✅ | `POST /taas/recommendation/accept/v1` |
| **Recommendation**: Override an AI transport recommendation with a reason | Staff | ✅ | `POST /taas/recommendation/override/v1` |
| **Transfer**: Create an inter-seller or inter-location transfer | Staff | 🖥️ | `POST /taas/transfer/stock/create/v1` |
| **Transfer**: Update transfer status | Staff | 🖥️ | `PATCH /taas/transfer/stock/status/update/v1` |
| **Transfer**: Confirm transfer received | Staff | 🖥️ | `POST /taas/transfer/stock/receive/v1` |
| **Refurbisher**: Ship an item to a refurbisher | Staff | 🖥️ | `POST /taas/refurbisher/shipment/create/v1` |
| **Partner**: Pass a shipment to the partner | Automatic | 🖥️ | `POST /taas/partner/shipment/relay/v1` |

#### Return routes (10)

Address: `/consumer/<role>/taas/returns`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Reverse**: Recommend the highest-value channel for a returned item | AI | 🖥️ | `POST /taas/reverse/route/recommend/v1` |
| **Reverse**: Route to resale | Staff | ✅ | `POST /taas/reverse/route/resale/assign/v1` |
| **Reverse**: Route to refurbishment | Staff | ✅ | `POST /taas/reverse/route/refurbish/assign/v1` |
| **Reverse**: Route to donation | Staff | ✅ | `POST /taas/reverse/route/donate/assign/v1` |
| **Reverse**: Route to parts harvesting | Staff | ✅ | `POST /taas/reverse/route/parts/assign/v1` |
| **Reverse**: Route to recycling | Staff | ✅ | `POST /taas/reverse/route/recycle/assign/v1` |
| **Reverse**: Schedule the pickup | Staff | ✅ | `POST /taas/reverse/pickup/schedule/v1` |
| **Reverse**: Plan the leg from a store drop-off | Staff | 🖥️ | `POST /taas/reverse/dropoff/store/leg/assign/v1` |
| **Pickup**: Plan the leg for store pickup instead of delivery | Staff | 🖥️ | `POST /taas/pickup/store-leg/assign/v1` |
| **Peer forward**: Match a resaleable return to the next buyer | Automatic | 🖥️ | `POST /taas/peer-forward/match/v1` |

#### Delivery rules (11)

Address: `/consumer/<role>/taas/delivery`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Delivery**: Set delivery options and rules | Root | ✅ | `PUT /taas/delivery/rules/set/v1` |
| **Delivery**: Suggest a delivery price | AI | 🖥️ | `POST /taas/delivery/pricing/dynamic/suggest/v1` |
| **Delivery**: Apply a suggested delivery price | Staff | 🖥️ | `POST /taas/delivery/pricing/dynamic/apply/v1` |
| **Route**: Choose the recommended green option | Staff | 🖥️ | `POST /taas/route/green/select/v1` |
| **Partner**: Use a partner's transport service | Root | 🖥️ | `POST /taas/partner/transport/enable/v1` |
| **Partner**: Offer own transport to partner Consumers | Root | 🖥️ | `POST /taas/partner/transport/offer/v1` |
| **Assistant**: Set delivery-assistant scope and modes | Root | 🖥️ | `PATCH /taas/assistant/config/update/v1` |
| **Personalization**: Show delivery options tailored to the Customer | Automatic | 🖥️ | `POST /taas/personalization/delivery-options/display/v1` |
| **Locale**: Set local or global delivery area | Root | ✅ | `PUT /taas/locale/service-area/set/v1` |
| **Locale**: Validate addresses by region | Automatic | 🖥️ | `POST /taas/locale/address/validate/v1` |
| **Locale**: Send delivery notices in the Customer's language | Automatic | 🖥️ | `POST /taas/locale/notification/language/send/v1` |

#### Insights (8)

Address: `/consumer/<role>/taas/insights`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Route**: Record emissions saved against the default route | Automatic | 🖥️ | `POST /taas/route/green/impact/v1` |
| **Fraud**: Flag address-change or failed-delivery abuse | Automatic | 🖥️ | `POST /taas/fraud/delivery/anomaly/detect/v1` |
| **Fraud**: Decide a flagged delivery case | Staff | 🖥️ | `POST /taas/fraud/review/decide/v1` |
| **Insights**: See delivery delays and complaints patterns | Staff | ✅ | `GET /taas/insights/delivery/read/v1` |
| **Analytics**: View delivery analytics | Staff | ✅ | `GET /taas/analytics/delivery/read/v1` |
| **Impact**: Record the default route and mode as baseline | Automatic | 🖥️ | `POST /taas/impact/baseline/record/v1` |
| **Impact**: View Transport-service impact | Root | ✅ | `GET /taas/impact/report/read/v1` |
| **Impact**: Generate the Transport-service impact report | Automatic | 🖥️ | `POST /taas/impact/report/generate/v1` |

### SaaS: Support as a Service (49 features)

#### Tickets (20)

Address: `/consumer/<role>/saas/tickets`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Ticket**: View tickets | Staff | ✅ | `GET /saas/ticket/read/staff/v1` |
| **Ticket**: Staff replies | Staff | ✅ | `POST /saas/ticket/reply/staff/v1` |
| **Ticket**: Assign a ticket | Staff | 🖥️ | `POST /saas/ticket/assign/v1` |
| **Ticket**: Update ticket status | Staff | ✅ | `PATCH /saas/ticket/status/update/v1` |
| **Ticket**: Escalate a ticket | Staff | 🖥️ | `POST /saas/ticket/escalate/v1` |
| **Ticket**: Close a ticket | Staff | ✅ | `POST /saas/ticket/close/v1` |
| **Dispute**: Respond to a dispute | Staff | 🖥️ | `POST /saas/dispute/respond/v1` |
| **Dispute**: Resolve a dispute | Staff | 🖥️ | `POST /saas/dispute/resolve/v1` |
| **Dispute**: Feed dispute outcomes into the seller trust score | Automatic | 🖥️ | `POST /saas/dispute/trust-score/feed/v1` |
| **Assistant**: Set support-assistant scope and modes | Root | 🖥️ | `PATCH /saas/assistant/config/update/v1` |
| **Scorecard**: See the Consumer's circularity scorecard | Root | 🖥️ | `GET /saas/scorecard/consumer/read/v1` |
| **Insights**: See common ticket issues and sentiment | Staff | 🖥️ | `GET /saas/insights/ticket-sentiment/read/v1` |
| **Analytics**: View support analytics | Staff | 🖥️ | `GET /saas/analytics/support/read/v1` |
| **Personalization**: Show a ticket view tailored to the Customer | Automatic | 🖥️ | `POST /saas/personalization/ticket-view/display/v1` |
| **Locale**: Translate tickets and replies | AI | 🖥️ | `POST /saas/locale/ticket/translate/v1` |
| **Locale**: Set region-specific return and repair policy | Root | 🖥️ | `PUT /saas/locale/policy/region/set/v1` |
| **Partner**: Use a partner's support service | Root | 🖥️ | `POST /saas/partner/support/enable/v1` |
| **Partner**: Pass a Customer's issue to a partner's support, while the Customer stays with their own Consumer | Staff | 🖥️ | `POST /saas/partner/issue/relay/v1` |
| **Partner**: Track the issue passed to the partner | Staff | 🖥️ | `GET /saas/partner/issue/status/read/v1` |
| **Impact**: View Support-service impact | Root | 🖥️ | `GET /saas/impact/report/read/v1` |

#### Returns and refunds (14)

Address: `/consumer/<role>/saas/returns`.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Return**: Set return rules | Root | ✅ | `PUT /saas/return/policy/set/v1` |
| **Return**: View return requests | Staff | ✅ | `GET /saas/return/request/read/v1` |
| **Return**: Approve a return | Staff | ✅ | `POST /saas/return/request/approve/v1` |
| **Return**: Reject a return | Staff | ✅ | `POST /saas/return/request/reject/v1` |
| **Return**: Issue a refund | Staff | ✅ | `POST /saas/return/refund/issue/v1` |
| **Triage**: Triage a return to the right path | AI | 🖥️ | `POST /saas/triage/return/route/v1` |
| **Grading**: Set grade and value thresholds | Root | 🖥️ | `PUT /saas/grading/threshold/set/v1` |
| **Grading**: Grade condition and predict recovery value from photos | AI | 🖥️ | `POST /saas/grading/photo/analyze/v1` |
| **Grading**: Staff override a grade | Staff | 🖥️ | `POST /saas/grading/result/override/v1` |
| **Fraud**: Screen returns and refunds for abuse | Automatic | 🖥️ | `POST /saas/fraud/return/screen/v1` |
| **Fraud**: View flagged returns | Staff | 🖥️ | `GET /saas/fraud/return/flag/read/v1` |
| **Fraud**: Decide a flagged return | Staff | 🖥️ | `POST /saas/fraud/review/decide/v1` |
| **Dropoff**: Staff verify the drop-off code | Staff | 🖥️ | `POST /saas/dropoff/store/receive/code-verify/v1` |
| **Dropoff**: Staff mark the item received | Staff | 🖥️ | `POST /saas/dropoff/store/receive/mark-received/v1` |

#### Repairs and recycling (15)

Address: `/consumer/<role>/saas/aftersales`. Repairs, refurbishers, trade-ins and recycling handovers.

| Feature | Who | Status | Endpoint |
|---|---|---|---|
| **Repair**: Set repair rules | Root | 🖥️ | `PUT /saas/repair/policy/set/v1` |
| **Repair**: Update repair progress | Staff | 🖥️ | `PATCH /saas/repair/status/update/v1` |
| **Trade in**: Complete the trade-in | Staff | 🖥️ | `POST /saas/trade-in/process/complete/v1` |
| **Recycling**: Estimate how much longer the item can be used | AI | 🖥️ | `POST /saas/recycling/lifespan/estimate/v1` |
| **Recycling**: Estimate how much can be recycled | AI | 🖥️ | `POST /saas/recycling/recyclable-share/estimate/v1` |
| **Recycling**: Record handover to a recycler | Staff | 🖥️ | `POST /saas/recycling/handover/record/v1` |
| **Recycling**: Issue a recycling certificate | Automatic | 🖥️ | `POST /saas/recycling/certificate/issue/v1` |
| **Parts**: Assess whether an item should be parts-harvested | AI | 🖥️ | `POST /saas/parts/harvest/assess/v1` |
| **Refurbisher**: Register a refurbisher's skills, capacity and location | Partner | 🖥️ | `POST /saas/refurbisher/profile/register/v1` |
| **Refurbisher**: Match items to refurbishers | AI | 🖥️ | `POST /saas/refurbisher/match/run/v1` |
| **Refurbisher**: A refurbisher bids for the work | Partner | 🖥️ | `POST /saas/refurbisher/bid/submit/v1` |
| **Refurbisher**: Assign the work | Staff | 🖥️ | `POST /saas/refurbisher/assign/v1` |
| **Impact**: Record what would have been landfilled without the AI route | Automatic | 🖥️ | `POST /saas/impact/baseline/record/v1` |
| **Impact**: Record the saving from each recovery event | Automatic | 🖥️ | `POST /saas/impact/event/record/v1` |
| **Impact**: Generate the Support-service impact report | Automatic | 🖥️ | `POST /saas/impact/report/generate/v1` |

### AI delivery planning (TaaS → Shipments → *Plan delivery with AI*)

Route (shortest, fastest, cheapest or greenest, with extra stops), vehicle (from load and distance, with the reasons others are ruled out), delivery date and time with a confidence range, and ranked delivery slots. Each comes with a plain-language explanation (summary, factors, confidence, data sources). Staff accept the pick or choose another with a reason, kept with who decided and when.

---

## 3. Customer

**Types:** Individual and Business (address `/customer/individual/...` or `/customer/business/...`). Demo: `customer@gmail.com` (Individual).

### Working today

- **Home page** (signed out): the four services, what each does, and a query form that reaches the Owner's *Queries* page. ✅
- **Storefront** (`/customer/individual/paas/catalog`): circular products with condition and price, and a live multi-seller bid on any product. ✅
- **AI shopping and support assistant**: opened from any product. ✅

### Catalog features (110, not built yet)

These are the Customer portal's features in the catalog. Each consumer chooses which of them its own customers get (Consumer → *Services and endpoints*), and the Customer portal is the next scope.

#### MaaS (18)

| Feature | Status | Endpoint |
|---|---|---|
| **Customer account**: Register an Individual account | ⏳ | `POST /maas/customer-account/register/individual/v1` |
| **Customer account**: Register a Business account | ⏳ | `POST /maas/customer-account/register/business/v1` |
| **Customer account**: Sign in (single sign-on across the Consumer's enabled services) | ⏳ | `POST /maas/customer-account/login/v1` |
| **Customer account**: View own profile | ⏳ | `GET /maas/customer-account/profile/read/v1` |
| **Customer account**: Update own profile | ⏳ | `PATCH /maas/customer-account/profile/update/v1` |
| **Customer account**: Deactivate own account | ⏳ | `POST /maas/customer-account/deactivate/v1` |
| **Assistant**: Ask the assistant about account and login questions (AI) | ⏳ | `POST /maas/assistant/account-help/ask/v1` |
| **Locale**: Choose own display language | ⏳ | `POST /maas/locale/language/customer-select/v1` |
| **Location**: See store locations | ⏳ | `GET /maas/location/store/list/v1` |
| **Customer account**: Verify the mail id used to register | ⏳ | `POST /maas/customer-account/mail/verify/v1` |
| **Customer account**: Sign out | ⏳ | `POST /maas/customer-account/logout/v1` |
| **Customer account**: Keep the sign-in session alive | ⏳ | `POST /maas/customer-account/session/refresh/v1` |
| **Customer account**: Request a password reset by mail | ⏳ | `POST /maas/customer-account/password/reset/request/v1` |
| **Customer account**: Set a new password from the reset mail | ⏳ | `POST /maas/customer-account/password/reset/confirm/v1` |
| **Customer account**: Change own password | ⏳ | `POST /maas/customer-account/password/change/v1` |
| **Customer account**: Export own data | ⏳ | `GET /maas/customer-account/data/export/v1` |
| **Customer account**: Request deletion of own data | ⏳ | `DELETE /maas/customer-account/data/delete/v1` |
| **Location**: Find the nearest store from the Customer's location | ⏳ | `GET /maas/location/store/nearby/find/v1` |

#### PaaS (52)

| Feature | Status | Endpoint |
|---|---|---|
| **Catalog**: View a product page | ⏳ | `GET /paas/catalog/product/view/v1` |
| **Catalog**: Search by text | ⏳ | `POST /paas/catalog/search/text/v1` |
| **Catalog**: Search by voice (AI) | ⏳ | `POST /paas/catalog/search/voice/v1` |
| **Catalog**: Snap a photo to find the same or similar item (AI) | ⏳ | `POST /paas/catalog/search/image/v1` |
| **Order**: Add an item to cart | ⏳ | `POST /paas/order/cart/add/v1` |
| **Order**: Remove an item from cart | ⏳ | `DELETE /paas/order/cart/remove/v1` |
| **Order**: View cart | ⏳ | `GET /paas/order/cart/read/v1` |
| **Order**: Place an order | ⏳ | `POST /paas/order/checkout/place/v1` |
| **Order**: View own orders | ⏳ | `GET /paas/order/read/customer/v1` |
| **Order**: Cancel own order | ⏳ | `POST /paas/order/cancel/customer/v1` |
| **Store stock**: See stock per store location | ⏳ | `GET /paas/store-stock/read/v1` |
| **Passport**: View a passport (origin, repairs, grades, carbon savings) | ⏳ | `GET /paas/passport/read/v1` |
| **Passport**: Scan a QR to open a passport | ⏳ | `GET /paas/passport/scan/v1` |
| **Bid**: Start an AI-assisted bid (AI) | ⏳ | `POST /paas/bid/ai/start/v1` |
| **Bid**: Customer replies to the bot (AI) | ⏳ | `POST /paas/bid/ai/customer-reply/v1` |
| **Bid**: Customer counters by voice (AI) | ⏳ | `POST /paas/bid/ai/counter-offer/voice/v1` |
| **Bid**: Start a human-only bid with the Consumer | ⏳ | `POST /paas/bid/human/start/v1` |
| **Bid**: Customer counters | ⏳ | `POST /paas/bid/human/counter/customer/v1` |
| **Bid**: Open a multi-seller bid request | ⏳ | `POST /paas/bid/multi-seller/open/v1` |
| **Bid**: View offers ranked by price, delivery, condition, reliability | ⏳ | `GET /paas/bid/multi-seller/rank/read/v1` |
| **Recommendation**: Get product recommendations (AI) | ⏳ | `GET /paas/recommendation/product/read/v1` |
| **Recommendation**: Get greener alternatives (AI) | ⏳ | `GET /paas/recommendation/sustainable/read/v1` |
| **Explain**: Read the plain-language reason for a price, award or recommendation (AI) | ⏳ | `GET /paas/explain/decision/read/v1` |
| **Assistant**: Shopping assistant, text in and text out (AI) | ⏳ | `POST /paas/assistant/chat/text-to-text/v1` |
| **Assistant**: Text in, spoken reply (AI) | ⏳ | `POST /paas/assistant/chat/text-to-speech/v1` |
| **Assistant**: Spoken in, text reply (AI) | ⏳ | `POST /paas/assistant/voice/speech-to-text/v1` |
| **Assistant**: Spoken in, spoken reply (AI) | ⏳ | `POST /paas/assistant/voice/speech-to-speech/v1` |
| **Pricing**: See a personalized offer (AI) | ⏳ | `GET /paas/pricing/personalized/offer/read/v1` |
| **Auction**: Bid in a surplus auction | ⏳ | `POST /paas/auction/surplus/bid/v1` |
| **Return risk**: Get size, fit or compatibility guidance before buying (AI) | ⏳ | `GET /paas/return-risk/checkout/guidance/read/v1` |
| **Future value**: See the guaranteed future buy-back value (AI) | ⏳ | `GET /paas/future-value/quote/read/v1` |
| **Future value**: Redeem the guarantee | ⏳ | `POST /paas/future-value/guarantee/redeem/v1` |
| **Environment**: View a product's environmental score | ⏳ | `GET /paas/environment/score/read/v1` |
| **Environment**: See the carbon impact of each offer | ⏳ | `GET /paas/environment/offer-score/read/v1` |
| **Environment**: See how recyclable a product is | ⏳ | `GET /paas/environment/recycling-factor/read/v1` |
| **Green credits**: View credit balance | ⏳ | `GET /paas/green-credits/balance/read/v1` |
| **Green credits**: Redeem credits | ⏳ | `POST /paas/green-credits/redeem/v1` |
| **Personalization**: Reset own profile data | ⏳ | `POST /paas/personalization/profile/reset/v1` |
| **Feedback**: Submit a review | ⏳ | `POST /paas/feedback/review/submit/v1` |
| **Basket**: See items often bought together (AI) | ⏳ | `GET /paas/basket/frequently-bought/read/v1` |
| **Reserve**: Reserve or pre-book an item online | ⏳ | `POST /paas/reserve/item/create/v1` |
| **Reserve**: View own reservations | ⏳ | `GET /paas/reserve/item/read/v1` |
| **Reserve**: Cancel a reservation | ⏳ | `POST /paas/reserve/item/cancel/v1` |
| **Pickup**: Choose a store for collection | ⏳ | `POST /paas/pickup/store/select/v1` |
| **Parts**: Browse parts | ⏳ | `GET /paas/parts/listing/read/v1` |
| **Payment**: General payment gateway: stands for a payment made through whichever third-party provider the Consumer uses (provider not specified by the Owner) | ⏳ | `POST /paas/payment/gateway/process/v1` |
| **Payment**: View an invoice for an order | ⏳ | `GET /paas/payment/invoice/read/v1` |
| **Promotion**: Apply a coupon at checkout | ⏳ | `POST /paas/promotion/coupon/apply/v1` |
| **Wishlist**: Add an item to the wishlist | ⏳ | `POST /paas/wishlist/item/add/v1` |
| **Wishlist**: Remove an item from the wishlist | ⏳ | `DELETE /paas/wishlist/item/remove/v1` |
| **Wishlist**: View the wishlist | ⏳ | `GET /paas/wishlist/read/v1` |
| **Feedback**: Read reviews on a product | ⏳ | `GET /paas/feedback/review/read/v1` |

#### TaaS (14)

| Feature | Status | Endpoint |
|---|---|---|
| **Delivery**: See delivery options | ⏳ | `GET /taas/delivery/option/list/v1` |
| **Delivery**: Choose a delivery option | ⏳ | `POST /taas/delivery/option/select/v1` |
| **Delivery**: Choose a delivery window | ⏳ | `POST /taas/delivery/window/select/v1` |
| **Tracking**: Track an order | ⏳ | `GET /taas/tracking/read/v1` |
| **Carbon**: See the delivery's carbon footprint (distance-based) | ⏳ | `GET /taas/carbon/footprint/delivery/read/v1` |
| **Carbon**: See the footprint of each offer's delivery | ⏳ | `GET /taas/carbon/footprint/offer/read/v1` |
| **Environment**: View environmental score of a transport option | ⏳ | `GET /taas/environment/transport-score/read/v1` |
| **Reverse**: Request pickup of a return | ⏳ | `POST /taas/reverse/pickup/request/v1` |
| **Peer forward**: Returner ships directly to the next buyer | ⏳ | `POST /taas/peer-forward/ship/v1` |
| **Peer forward**: Next buyer confirms receipt | ⏳ | `POST /taas/peer-forward/confirm/v1` |
| **Assistant**: Ask about delivery by text (AI) | ⏳ | `POST /taas/assistant/delivery/text-to-text/v1` |
| **Assistant**: Text in, spoken reply (AI) | ⏳ | `POST /taas/assistant/delivery/text-to-speech/v1` |
| **Assistant**: Spoken in, text reply (AI) | ⏳ | `POST /taas/assistant/delivery/speech-to-text/v1` |
| **Assistant**: Spoken in, spoken reply (AI) | ⏳ | `POST /taas/assistant/delivery/speech-to-speech/v1` |

#### SaaS (26)

| Feature | Status | Endpoint |
|---|---|---|
| **Ticket**: Raise a query | ⏳ | `POST /saas/ticket/create/query/v1` |
| **Ticket**: Raise a return ticket | ⏳ | `POST /saas/ticket/create/return/v1` |
| **Ticket**: Raise a repair ticket | ⏳ | `POST /saas/ticket/create/repair/v1` |
| **Ticket**: Raise a trade-in ticket | ⏳ | `POST /saas/ticket/create/trade-in/v1` |
| **Ticket**: View own tickets | ⏳ | `GET /saas/ticket/read/customer/v1` |
| **Ticket**: Customer replies | ⏳ | `POST /saas/ticket/reply/customer/v1` |
| **Ticket**: Track after-sales progress | ⏳ | `GET /saas/ticket/status/read/v1` |
| **Return**: Start a guided return | ⏳ | `POST /saas/return/request/create/v1` |
| **Repair**: Request a repair | ⏳ | `POST /saas/repair/request/create/v1` |
| **Grading**: Submit photos of the item | ⏳ | `POST /saas/grading/photo/submit/v1` |
| **Grading**: See the grade and value before shipping | ⏳ | `GET /saas/grading/result/read/v1` |
| **Trade in**: Request a trade-in | ⏳ | `POST /saas/trade-in/request/create/v1` |
| **Trade in**: See the trade-in value (AI) | ⏳ | `GET /saas/trade-in/valuation/read/v1` |
| **Trade in**: Accept the trade-in offer | ⏳ | `POST /saas/trade-in/offer/accept/v1` |
| **Recycling**: Request recycling | ⏳ | `POST /saas/recycling/request/create/v1` |
| **Recommendation**: Get reuse or repair advice (AI) | ⏳ | `GET /saas/recommendation/reuse/read/v1` |
| **Recommendation**: Get recycling advice (AI) | ⏳ | `GET /saas/recommendation/recycle/read/v1` |
| **Explain**: Read the reason for a grade or route (AI) | ⏳ | `GET /saas/explain/decision/read/v1` |
| **Dispute**: Open a dispute with the Consumer | ⏳ | `POST /saas/dispute/open/v1` |
| **Assistant**: Ask support by text (AI) | ⏳ | `POST /saas/assistant/support/text-to-text/v1` |
| **Assistant**: Text in, spoken reply (AI) | ⏳ | `POST /saas/assistant/support/text-to-speech/v1` |
| **Assistant**: Spoken in, text reply (AI) | ⏳ | `POST /saas/assistant/support/speech-to-text/v1` |
| **Assistant**: Spoken in, spoken reply (AI) | ⏳ | `POST /saas/assistant/support/speech-to-speech/v1` |
| **Scorecard**: See own value recovered, waste diverted, carbon saved | ⏳ | `GET /saas/scorecard/customer/read/v1` |
| **Dropoff**: Start a return, repair or trade-in online and drop off at a store | ⏳ | `POST /saas/dropoff/store/create/v1` |
| **Dropoff**: Track the drop-off online | ⏳ | `GET /saas/dropoff/status/read/v1` |

---

## Not in place yet (planned with the backend)

- Real sign-in with tokens. Today the signed-in email is trusted as sent.
- Invited staff signing in from their invite, and reactivating deactivated roles.
- Real handlers for the 🖥️ features, and running the automatic and AI ones on their own events.
- The Customer portal (the ⏳ features above).
- Persistent storage. All data is in memory, so a backend restart resets it to the demo values.
