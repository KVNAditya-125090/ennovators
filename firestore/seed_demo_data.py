"""
Firestore - demo data.
Fills the demo consumer (Lakshmi Demo Retail) with made-up records so every screen has something to show: products with
pictures, orders, shipments, support tickets, returns, stores, parts, product passports, reviews, delivery options,
settings, the demo shopper's own history, and the platform-side queries and tickets the Owner sees.

Everything is invented: people, addresses, phone numbers and figures. Emails use the reserved .example domain. Every
record has a fixed id, so running this again replaces the same records and never adds a second copy.

    python -m firestore.seed_demo_data            add or refresh the demo data
    python -m firestore.seed_demo_data --remove   take it all out again (the accounts are not touched)

Product videos are not part of the demo data: only pictures.
"""

import datetime
import io
import os
import sys
from typing import Any, Dict, List

from cloud_run.ids import passport_id, seed_id
from cloud_sql.services.maas import cloud_sql_maas as maas
from cloud_sql.services.maas.roles import roles as role_store
from cloud_storage import media_store
from firestore import store

CONSUMER = "Lakshmi Demo Retail"
SHOPPER = "individual.customer@gmail.com"
TODAY = datetime.date.today()

def day(n: int) -> str:
    return (TODAY - datetime.timedelta(days=n)).isoformat()

def sid(kind: str, key: str) -> str:
    return seed_id(f"demo:{kind}:{key}")

# ---------------------------------------------------------------- stores
STORES = [
    ("pune", "Lakshmi Pune (Baner)", "12 Demo Street, Baner, Pune 411045", "Pune", 18.559, 73.780),
    ("mumbai", "Lakshmi Mumbai (Bandra)", "7 Sample Road, Bandra West, Mumbai 400050", "Mumbai", 19.054, 72.840),
    ("hyderabad", "Lakshmi Hyderabad (Jubilee Hills)", "30 Example Avenue, Jubilee Hills, Hyderabad 500033", "Hyderabad", 17.431, 78.409),
]

# ---------------------------------------------------------------- products: key, name, sku, category, price, condition, stock, co2 saved, recyclable %, colour, label
PRODUCTS = [
    ("phone", "Refurbished Smartphone 128 GB", "SKU-PHN-A1", "Phones", 189.00, "Certified Refurbished (Grade A)", 14, 52.0, 88, (66, 133, 244), "PHONE"),
    ("laptop", "Refurbished Laptop 14-inch, 8 GB", "SKU-LAP-14", "Computers", 329.00, "Certified Refurbished (Grade A)", 7, 180.0, 82, (52, 168, 83), "LAPTOP"),
    ("tablet", "Refurbished Tablet 10-inch", "SKU-TAB-10", "Computers", 149.00, "Certified Refurbished (Grade B)", 9, 70.0, 85, (251, 188, 4), "TABLET"),
    ("watch", "Smart Watch (open box)", "SKU-WCH-S3", "Wearables", 99.00, "Open-box Excellent", 11, 18.0, 70, (234, 67, 53), "WATCH"),
    ("headphones", "Noise-Cancelling Headphones (refurbished)", "SKU-AUD-NC", "Audio", 79.00, "Certified Refurbished (Grade A)", 8, 14.0, 78, (26, 115, 232), "HEADPHONES"),
    ("earbuds", "Wireless Earbuds (refurbished)", "SKU-AUD-EB", "Audio", 39.00, "Certified Refurbished (Grade A)", 20, 7.0, 72, (161, 66, 244), "EARBUDS"),
    ("speaker", "Bluetooth Speaker (refurbished)", "SKU-SPK-BT", "Audio", 45.00, "Certified Refurbished (Grade B)", 12, 9.0, 80, (255, 112, 67), "SPEAKER"),
    ("powerbank", "Solar Power Bank 20,000 mAh", "SKU-PWR-SL", "Power", 59.00, "New / Factory Sealed", 25, 5.0, 90, (0, 150, 136), "POWER BANK"),
    ("lamp", "Solar LED Desk Lamp", "SKU-LMP-SL", "Home", 24.00, "New / Factory Sealed", 30, 3.0, 92, (255, 193, 7), "SOLAR LAMP"),
    ("kettle", "Electric Kettle 1.5 L (refurbished)", "SKU-KTL-E1", "Home", 19.00, "Certified Refurbished (Grade A)", 16, 6.0, 84, (121, 85, 72), "KETTLE"),
    ("mixer", "Mixer Grinder 3-jar (refurbished)", "SKU-MXR-G3", "Home", 42.00, "Certified Refurbished (Grade B)", 10, 11.0, 86, (96, 125, 139), "MIXER"),
    ("purifier", "Air Purifier (refurbished)", "SKU-APF-HP", "Home", 119.00, "Certified Refurbished (Grade A)", 5, 25.0, 80, (3, 169, 244), "AIR PURIFIER"),
]
KEYS = [p[0] for p in PRODUCTS]
def product_id(key: str) -> str:
    return sid("product", key)

def picture(label: str, colour) -> bytes:
    from PIL import Image, ImageDraw, ImageFont
    w, h = 640, 480
    img = Image.new("RGB", (w, h), colour)
    d = ImageDraw.Draw(img)
    for i in range(h):  # a soft top-to-bottom shade
        shade = int(60 * i / h)
        d.line([(0, i), (w, i)], fill=tuple(max(0, c - shade) for c in colour))
    d.ellipse([w // 2 - 130, 70, w // 2 + 130, 330], outline=(255, 255, 255), width=10)
    font = ImageFont.load_default(size=44)
    small = ImageFont.load_default(size=24)
    box = d.textbbox((0, 0), label, font=font)
    d.text(((w - (box[2] - box[0])) / 2, 190), label, fill=(255, 255, 255), font=font)
    tag = "Lakshmi demo picture"
    box = d.textbbox((0, 0), tag, font=small)
    d.text(((w - (box[2] - box[0])) / 2, 400), tag, fill=(255, 255, 255), font=small)
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()

def media_name(key: str) -> str:
    return sid("picture", key).replace("-", "") + ".png"

# ---------------------------------------------------------------- people (invented)
PEOPLE = [
    ("Aarav Sharma", "aarav.sharma@mail.example"), ("Diya Patel", "diya.patel@mail.example"), ("Rohan Mehta", "rohan.mehta@mail.example"),
    ("Ananya Iyer", "ananya.iyer@mail.example"), ("Kabir Singh", "kabir.singh@mail.example"), ("Meera Nair", "meera.nair@mail.example"),
    ("Vikram Rao", "vikram.rao@mail.example"), ("Isha Gupta", "isha.gupta@mail.example"), ("Arjun Reddy", "arjun.reddy@mail.example"),
    ("Sneha Kulkarni", "sneha.kulkarni@mail.example"), ("Rahul Verma", "rahul.verma@mail.example"), ("Priya Menon", "priya.menon@mail.example"),
]
DEMO_NAME = "Individual Customer"

# orders: key, who (index into PEOPLE or None for the demo shopper), [(product key, qty)], status, days ago
ORDERS = [
    ("o01", 0, [("phone", 1)], "delivered", 41), ("o02", 1, [("headphones", 1), ("earbuds", 1)], "delivered", 38),
    ("o03", 2, [("laptop", 1)], "delivered", 35), ("o04", 3, [("lamp", 2)], "delivered", 31),
    ("o05", None, [("watch", 1)], "delivered", 29), ("o06", 4, [("speaker", 1)], "cancelled", 27),
    ("o07", 5, [("tablet", 1)], "delivered", 24), ("o08", 6, [("kettle", 1), ("mixer", 1)], "delivered", 21),
    ("o09", 7, [("powerbank", 1)], "shipped", 12), ("o10", 8, [("purifier", 1)], "shipped", 10),
    ("o11", None, [("earbuds", 2)], "shipped", 7), ("o12", 9, [("phone", 1)], "shipped", 6),
    ("o13", 10, [("lamp", 1), ("powerbank", 1)], "paid", 4), ("o14", 11, [("tablet", 1)], "paid", 3),
    ("o15", 0, [("speaker", 1)], "paid", 2), ("o16", None, [("headphones", 1)], "placed", 1),
    ("o17", 2, [("kettle", 2)], "placed", 1), ("o18", 3, [("watch", 1)], "cancelled", 0),
]
ORDER_ID = {o[0]: sid("order", o[0]) for o in ORDERS}

CARRIERS = [("Lakshmi Electric Express", "electric van", True), ("GreenRoute Logistics", "electric bike", True), ("Relay Partner Network", "diesel van", False)]
CITIES = ["Pune", "Mumbai", "Hyderabad", "Nashik", "Thane", "Secunderabad"]

def build() -> Dict[str, Any]:
    price = {p[0]: p[4] for p in PRODUCTS}
    name = {p[0]: p[1] for p in PRODUCTS}
    store_ids = [sid("store", s[0]) for s in STORES]

    stores = [{"store_id": sid("store", k), "name": n, "address": a, "city": c, "country": "India", "latitude": la, "longitude": lo,
               "opening_hours": "Mon-Sat 10:00-19:00", "active": True} for k, n, a, c, la, lo in STORES]

    products = []
    for key, pname, sku, cat, pr, cond, stock, co2, rec, _, _ in PRODUCTS:
        url = f"{os.environ.get('PUBLIC_API_URL', 'https://lakshmi-backend-668647657342.us-central1.run.app').rstrip('/')}/api/v1/media/{{tenant}}/{media_name(key)}"
        split = [stock // 3 + (1 if i < stock % 3 else 0) for i in range(3)]
        products.append({"id": product_id(key), "name": pname, "sku": sku, "category": cat, "description": f"{pname}. Tested, cleaned and covered by a 12-month Lakshmi demo warranty.",
                         "retail_price": pr, "current_bidding_floor": round(pr * 0.72, 2), "condition": cond, "stock": stock,
                         "carbon_footprint_kg": co2, "recyclable_pct": rec, "images": [url], "videos": [], "image_url": url,
                         "stock_by_store": {store_ids[i]: split[i] for i in range(3)}})

    orders, shipments, shopper_orders = [], [], []
    for n, (key, who, lines, status, ago) in enumerate(ORDERS):
        cname, email = (DEMO_NAME, SHOPPER) if who is None else PEOPLE[who]
        total = round(sum(price[k] * q for k, q in lines), 2)
        orders.append({"order_id": ORDER_ID[key], "customer": cname, "customer_email": email, "items": ", ".join(f"{name[k]} x{q}" for k, q in lines),
                       "lines": [{"product_id": product_id(k), "name": name[k], "price": price[k], "quantity": q} for k, q in lines],
                       "total": total, "status": status, "placed": day(ago)})
        if who is None:
            shopper_orders.append({"order_id": ORDER_ID[key], "lines": [{"product_id": product_id(k), "name": name[k], "price": price[k], "quantity": q} for k, q in lines],
                                   "total_usd": total, "status": status, "payment_method": "card", "address": {"line": "21 Demo Lane, Pune 411001"},
                                   "placed_at": day(ago) + " 11:30", "seller": CONSUMER})
        if status in ("shipped", "delivered", "paid") and status != "paid":
            carrier, mode, electric = CARRIERS[n % 3]
            origin = STORES[n % 3][1]
            dest = CITIES[n % len(CITIES)]
            delivered = status == "delivered"
            co2 = round(0.4 + 0.1 * (n % 5), 1) if electric else round(1.6 + 0.1 * (n % 4), 1)
            events = [{"at": day(ago - 1) + " 09:10", "event": "Picked up at " + origin}, {"at": day(ago - 1) + " 18:40", "event": f"At the {dest} hub"}]
            if delivered:
                events.append({"at": day(max(ago - 3, 0)) + " 13:25", "event": "Delivered"})
            else:
                events.append({"at": day(max(ago - 2, 0)) + " 07:05", "event": "Out for delivery"})
            shipments.append({"shipment_id": sid("shipment", key), "order_id": ORDER_ID[key], "type": "Forward Delivery", "origin": origin, "destination": f"{cname} ({dest})",
                              "status": "delivered" if delivered else "in_transit", "carrier": carrier, "mode": mode, "electric": electric,
                              "eta": "Delivered " + day(max(ago - 3, 0)) if delivered else "In 1-2 days", "co2_kg": co2, "co2_saved_kg": round(2.4 - co2, 1) if electric else 0.0,
                              "carbon_note": f"Delivered by {mode}.", "events": events, "placed": day(ago), "delivered": day(max(ago - 3, 0)) if delivered else None,
                              "on_time": (n % 7 != 3) if delivered else None})
    shipments.append({"shipment_id": sid("shipment", "o13"), "order_id": ORDER_ID["o13"], "type": "Forward Delivery", "origin": STORES[0][1], "destination": f"{PEOPLE[10][0]} (Pune)",
                      "status": "created", "carrier": CARRIERS[0][0], "mode": CARRIERS[0][1], "electric": True, "eta": "In 3 days", "co2_kg": 0.5, "co2_saved_kg": 1.9,
                      "carbon_note": "Delivered by electric van.", "events": [{"at": day(3) + " 16:00", "event": "Shipment created"}]})

    def t(key, cust, email, subject, status, thread):
        return {"ticket_id": sid("ticket", key), "customer": cust, "customer_email": email, "subject": subject, "type": "query", "status": status,
                "messages": [{"from": f, "author": a, "text": x} if a else {"from": f, "text": x} for f, a, x in thread]}
    tickets = [
        t("t01", DEMO_NAME, SHOPPER, "Watch strap feels loose", "in_progress", [("Customer", None, "The strap on my smart watch feels loose after a week."), ("Staff", "Support", "Sorry about that. Could you send a photo of the clasp?")]),
        t("t02", PEOPLE[1][0], PEOPLE[1][1], "Left earbud is quiet", "open", [("Customer", None, "The left earbud is much quieter than the right one.")]),
        t("t03", PEOPLE[2][0], PEOPLE[2][1], "Invoice copy needed", "resolved", [("Customer", None, "Please resend my invoice."), ("Staff", "Support", "Sent to your email.")]),
        t("t04", PEOPLE[3][0], PEOPLE[3][1], "Lamp does not switch on", "open", [("Customer", None, "The solar lamp will not switch on, even after a day in the sun.")]),
        t("t05", PEOPLE[5][0], PEOPLE[5][1], "Warranty question for the tablet", "closed", [("Customer", None, "How long is the warranty?"), ("Staff", "Support", "12 months from delivery."), ("Staff", "Support", "Resolution: warranty terms explained.")]),
        t("t06", PEOPLE[6][0], PEOPLE[6][1], "Change my delivery address", "in_progress", [("Customer", None, "Can I deliver to my office instead?"), ("Staff", "Operation", "Checking with the carrier.")]),
        t("t07", PEOPLE[7][0], PEOPLE[7][1], "Return label not received", "open", [("Customer", None, "I asked for a return label two days ago.")]),
        t("t08", PEOPLE[0][0], PEOPLE[0][1], "Phone battery drains fast", "in_progress", [("Customer", None, "Battery lasts about half a day."), ("Staff", "Support", "That is below our standard. A free battery check is possible at any store.")]),
    ]
    returns = [
        {"return_id": sid("return", "r01"), "order_id": ORDER_ID["o05"], "customer": DEMO_NAME, "item": name["watch"], "reason": "Strap too loose", "amount": price["watch"], "status": "requested"},
        {"return_id": sid("return", "r02"), "order_id": ORDER_ID["o02"], "customer": PEOPLE[1][0], "item": name["earbuds"], "reason": "Left earbud is quiet", "amount": price["earbuds"], "status": "approved", "route": "refurbish"},
        {"return_id": sid("return", "r03"), "order_id": ORDER_ID["o04"], "customer": PEOPLE[3][0], "item": name["lamp"], "reason": "Does not switch on", "amount": price["lamp"] * 2, "status": "refunded", "refunded": price["lamp"] * 2, "route": "recycle"},
        {"return_id": sid("return", "r04"), "order_id": ORDER_ID["o07"], "customer": PEOPLE[5][0], "item": name["tablet"], "reason": "Changed my mind", "amount": price["tablet"], "status": "rejected", "reject_reason": "Outside the 30-day return window"},
        {"return_id": sid("return", "r05"), "order_id": ORDER_ID["o01"], "customer": PEOPLE[0][0], "item": name["phone"], "reason": "Battery drains fast", "amount": price["phone"], "status": "approved", "route": "refurbish"},
        {"return_id": sid("return", "r07"), "order_id": ORDER_ID["o15"], "customer": PEOPLE[0][0], "item": name["speaker"], "reason": "Sound is distorted", "amount": price["speaker"], "status": "requested"},
        {"return_id": sid("return", "r06"), "order_id": ORDER_ID["o08"], "customer": PEOPLE[6][0], "item": name["mixer"], "reason": "Jar cracked on arrival", "amount": price["mixer"], "status": "requested"},
    ]
    parts = [{"part_id": sid("part", k), "name": n, "price": p, "condition": c, "fits": f} for k, n, p, c, f in [
        ("battery", "Replacement battery module", 24.0, "new", "Smart watch, smartphone"), ("strap", "Eco strap (recycled)", 12.5, "new", "Smart watch"),
        ("charger", "USB-C charger 20 W (salvaged, tested)", 8.0, "salvaged", "Phone, tablet, earbuds case"), ("screen", "Laptop 14-inch screen (salvaged)", 45.0, "salvaged", "Refurbished laptop 14-inch"),
        ("jar", "Mixer grinder jar set", 14.0, "new", "Mixer grinder 3-jar")]]
    passports = [{"passport_id": passport_id(product_id(p[0])), "origin": f"Collected as a return in {CITIES[i % 3]}, refurbished in Pune",
                  "owners": 1 + i % 2, "repairs": [{"at": day(120 + i), "note": "Battery or wear parts replaced and certified"}],
                  "grades": [{"at": day(110 + i), "grade": "A" if "Grade A" in p[5] or "New" in p[5] else "B", "note": "Cleaned, tested and graded"}],
                  "carbon_saved_kg": p[7], "recyclable_pct": p[8]} for i, p in enumerate(PRODUCTS)]
    review_text = [(5, "Works like new and saved a lot of money."), (4, "Good condition, small mark on the back."), (5, "Fast delivery and well packed."), (3, "Fine, but the battery is not as strong as new.")]
    reviews = []
    for i, k in enumerate(KEYS):
        for j in range(2):
            rating, text = review_text[(i + j) % 4]
            who = PEOPLE[(i + j * 5) % len(PEOPLE)][0]
            reviews.append({"review_id": sid("review", f"{k}{j}"), "product_id": product_id(k), "rating": rating, "comment": text, "by": who, "at": day(10 + i + j)})
    reviews.append({"review_id": sid("review", "demo-watch"), "product_id": product_id("watch"), "rating": 4, "comment": "Looks great. The strap is a little loose.", "by": DEMO_NAME, "at": day(20)})

    config = {
        "delivery_options": {"options": [
            {"option_id": sid("delivery", "eco"), "name": "Eco (electric van)", "days": 3, "price_usd": 0.0, "carbon_kg": 0.4, "environmental_score": 95},
            {"option_id": sid("delivery", "standard"), "name": "Standard", "days": 2, "price_usd": 2.5, "carbon_kg": 1.2, "environmental_score": 70},
            {"option_id": sid("delivery", "express"), "name": "Express", "days": 1, "price_usd": 6.0, "carbon_kg": 2.8, "environmental_score": 45}]},
        "delivery_rules": {"options": ["Standard (3-5 days)", "Express (1-2 days)", "Store pickup"], "cutoff_time": "16:00", "regions": ["Maharashtra", "Telangana", "Karnataka"]},
        "service_area": {"mode": "local", "regions": ["Maharashtra", "Telangana", "Karnataka"]},
        "return_policy": {"window_days": 30, "conditions": ["unused", "original packaging"], "refund_method": "original"},
        "settings": {"company_name": "Lakshmi Demo Retail Pvt Ltd (demo)", "contact_mail": "it.consumer@lakshmi.com", "timezone": "IST (UTC+5:30)",
                     "default_language": "English", "default_currency": "USD"},
    }

    shopper = {
        "profile": {"email": SHOPPER, "account_type": "individual", "full_name": DEMO_NAME, "phone": "+91 90000 00001", "preferred_language": "en",
                    "address": {"line": "21 Demo Lane, Pune 411001"}, "verified": True, "consumer": CONSUMER, "joined": day(60) + " 10:00"},
        "cart": [{"product_id": product_id("speaker"), "name": name["speaker"], "price": price["speaker"], "quantity": 1}],
        "wishlist": [{"product_id": product_id("laptop"), "name": name["laptop"], "price": price["laptop"]}, {"product_id": product_id("purifier"), "name": name["purifier"], "price": price["purifier"]}],
        "orders": shopper_orders,
        "tickets": [{"ticket_id": sid("ticket", "t01"), "type": "query", "subject": "Watch strap feels loose", "status": "open", "order_id": ORDER_ID["o05"], "product_id": product_id("watch"),
                     "messages": [{"by": SHOPPER, "message": "The strap on my smart watch feels loose after a week.", "at": day(5) + " 10:00"}], "at": day(5) + " 10:00", "consumer": CONSUMER}],
        "reservations": [{"reservation_id": sid("reservation", "r1"), "product_id": product_id("tablet"), "name": name["tablet"], "store_id": sid("store", "pune"),
                          "pickup_by": day(-2), "status": "reserved", "at": day(1) + " 15:00"}],
        "reviews": [r for r in reviews if r["by"] == DEMO_NAME], "green_credits": 120, "bids": [],
    }

    platform_tickets = [
        {"ticket_id": sid("ptk", "p1"), "tenant_id": "{tenant}", "consumer": CONSUMER, "subject": "Photo grading results look inconsistent", "priority": "High", "status": "Open", "opened": day(9), "first_response_hours": 1.5, "resolution_hours": None},
        {"ticket_id": sid("ptk", "p2"), "tenant_id": "{tenant}", "consumer": CONSUMER, "subject": "Invoice shows the wrong API fee", "priority": "Low", "status": "Resolved", "opened": day(14), "first_response_hours": 4.0, "resolution_hours": 26.0},
        {"ticket_id": sid("ptk", "p3"), "tenant_id": "{tenant}", "consumer": CONSUMER, "subject": "Question about reorder point settings", "priority": "Normal", "status": "Open", "opened": day(8), "first_response_hours": None, "resolution_hours": None},
    ]
    q = [("Priya Nair", "priya.nair@mail.example", "+91 90000 00112", "Can your platform manage stock across several warehouses for a refurbished electronics store?", 9, "New", None),
         ("Rahul Verma", "rahul.verma2@mail.example", "+91 90000 00111", "Is there an integration with Shopify?", 9, "New", None),
         ("Hannah Fischer", "hannah.fischer@mail.example", "+49 150 0000 0110", "Do you offer a free trial for small retailers?", 10, "New", None),
         ("Daniel Okafor", "daniel.okafor@mail.example", "+234 800 000 0109", "I would like a demo of the return grading AI for my repair shop.", 11, "In conversation", 3.0),
         ("Liam Carter", "liam.carter@mail.example", "+1 555 010 0108", "We need help moving 4,000 products onto the catalog in one go.", 13, "In conversation", 1.8),
         ("Aisha Khan", "aisha.khan@mail.example", "+971 50 000 0107", "Can the shipment tracking cover cross-border returns?", 16, "In conversation", 2.4),
         ("Mei Tanaka", "mei.tanaka@mail.example", "+81 90 0000 0106", "What are the pricing options for a small retailer?", 19, "Closed", 1.5),
         ("Sofia Alvarez", "sofia.alvarez@mail.example", "+34 600 000 105", "How do I become a platform consumer?", 22, "Closed", 2.2)]
    queries = [{"query_id": sid("query", str(i)), "name": a, "email": b, "mobile": c, "message": d, "received": day(e), "status": f, "first_response_hours": g}
               for i, (a, b, c, d, e, f, g) in reversed(list(enumerate(q)))]  # oldest first: the store keeps the order they are saved in

    # sample records for the screens whose features have nothing behind them yet (partners, API keys, account checks)
    def item(ident, **fields):
        return {"id": sid("preview", ident), "params": {}, "status": "sample", **fields}
    preview = {
        "MaaS__partner": [
            item("partner1", partner="GreenFix Repairs (sample partner)", link="Repairs and refurbishment", state="Enabled", customer_access=True, since=day(40)),
            item("partner2", partner="CityRelay Delivery (sample partner)", link="Last-mile delivery", state="Waiting for the Owner", customer_access=False, since=day(6)),
            item("call1", partner="GreenFix Repairs (sample partner)", call="Repair request relayed", direction="outgoing", at=day(3) + " 14:20", result="Accepted"),
            item("call2", partner="GreenFix Repairs (sample partner)", call="Repair status read", direction="outgoing", at=day(2) + " 09:05", result="In progress")],
        "MaaS__fraud": [
            item("acct1", account="rohan.mehta@mail.example", signal="Five sign-in attempts from three cities in one hour", score=72, state="Waiting for review", seen=day(2)),
            item("acct2", account="isha.gupta@mail.example", signal="Several accounts created from one address", score=55, state="Waiting for review", seen=day(5))],
        "MaaS__api-key": [
            item("key1", name="Storefront (sample key)", key="lk_live_****7a2f", created=day(50), last_used=day(0), state="Active"),
            item("key2", name="Warehouse scanner (sample key)", key="lk_live_****c91d", created=day(30), last_used=day(4), state="Active")],
        "MaaS__service-identity": [
            item("sid1", step="Demand forecast job (automatic)", may_call=["/paas/forecast/demand/run/v1", "/paas/forecast/reorder/suggest/v1"], state="Limited"),
            item("sid2", step="Return grading (AI)", may_call=["/saas/grading/photo/analyze/v1", "/saas/triage/return/route/v1"], state="Limited")],
    }

    return {"preview": preview, "stores": stores, "products": products, "orders": orders, "shipments": shipments, "tickets": tickets, "returns": returns, "parts": parts,
            "passports": passports, "reviews": reviews, "config": config, "shopper": shopper, "platform_tickets": platform_tickets, "queries": queries}

def upsert(rows: List[Dict[str, Any]], key: str, wanted: List[Dict[str, Any]]) -> None:
    """Puts each wanted record in its place by id: a record that is already there is replaced, not copied."""
    at = {str(r[key]): i for i, r in enumerate(rows)}
    for record in wanted:
        i = at.get(str(record[key]))
        if i is None:
            rows.append(record)
        else:
            rows[i].clear(); rows[i].update(record)

def delete_ids(rows: List[Dict[str, Any]], key: str, wanted: List[Dict[str, Any]]) -> int:
    ids = {str(r[key]) for r in wanted}
    keep = [r for r in rows if str(r[key]) not in ids]
    removed = len(rows) - len(keep)
    rows[:] = keep
    return removed

def main(remove: bool = False) -> int:
    tenant = maas.get_tenant_by_name(CONSUMER)
    if tenant is None:
        print(f"The consumer {CONSUMER} does not exist. Run: python -m cloud_sql.seed_demo")
        return 1
    tid = tenant["tenant_id"]
    data = build()
    for p in data["products"]:
        for field in ("images", "image_url"):
            v = p[field]; p[field] = [x.replace("{tenant}", tid) for x in v] if isinstance(v, list) else v.replace("{tenant}", tid)
    for t in data["platform_tickets"]:
        t["tenant_id"] = tid

    token = store.begin()
    store.set_tenant(tid)
    tenant_sets = [("stores", "store_id"), ("products", "id"), ("orders", "order_id"), ("shipments", "shipment_id"), ("tickets", "ticket_id"),
                   ("returns", "return_id"), ("parts", "part_id"), ("passports", "passport_id"), ("reviews", "review_id")]
    order_new_first = {"orders", "tickets", "returns", "reviews"}
    if remove:
        total = 0
        for name, key in tenant_sets:
            total += delete_ids(store.rows(name, key, newest_first=name in order_new_first), key, data[name])
        total += delete_ids(store.rows("platform_tickets", "ticket_id", scope="global", newest_first=True), "ticket_id", data["platform_tickets"])
        total += delete_ids(store.rows("queries", "query_id", scope="global", newest_first=True), "query_id", data["queries"])
        for name in data["config"]:
            store.drop("config", name)
        store.drop("shoppers", SHOPPER)
        for name in data["preview"]:
            store.drop("preview", name)
        for p in PRODUCTS:
            try:
                media_store.delete(tid, media_name(p[0]))
            except Exception:
                pass
        written = store.flush()
        print(f"Removed {total} records, the demo shopper's history, the settings and the pictures ({written} writes).")
        store.end(token)
        return 0

    for p in PRODUCTS:
        media_store.put(tid, media_name(p[0]), picture(p[10], p[9]), "image/png")
    for name, key in tenant_sets:
        upsert(store.rows(name, key, newest_first=name in order_new_first), key, data[name])
    upsert(store.rows("platform_tickets", "ticket_id", scope="global", newest_first=True), "ticket_id", data["platform_tickets"])
    upsert(store.rows("queries", "query_id", scope="global", newest_first=True), "query_id", data["queries"])
    for name, value in data["config"].items():
        doc = store.kdoc("config", name, dict); doc.clear(); doc.update(value)
    for name, items in data["preview"].items():
        doc = store.kdoc("preview", name, lambda: {"items": []}); doc["items"] = items
    shopper = store.kdoc("shoppers", SHOPPER, dict); shopper.clear(); shopper.update(data["shopper"])
    written = store.flush()
    store.end(token)
    for event, message in [("role-created", "The Marketing role was created."), ("role-created", "The Operation role was created."), ("role-created", "The Support role was created."),
                           ("template-published", "The customer storefront was published as version 1.")]:
        if not any(m["message"] == message for m in role_store.mail_log(tid)):
            role_store.log_mail(tid, event, None, "Root", message)
    counts = {k: len(v) for k, v in data.items() if isinstance(v, list)}
    print(f"Demo data written ({written} documents): {counts}, plus settings, delivery options and the shopper's history.")
    return 0

if __name__ == "__main__":
    sys.exit(main("--remove" in sys.argv))
