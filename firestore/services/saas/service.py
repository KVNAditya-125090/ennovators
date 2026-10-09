"""
Firestore - SaaS (Support as a Service)
Document collections: support tickets, and queries from the home page.
"""

import datetime
from typing import Dict, Any, List, Optional

TICKETS = [
    {"ticket_id": "TCK-501", "customer": "Marcus Vance", "topic": "Return Photo Triage", "status": "AI Auto-Approved (Grade A)", "priority": "Normal", "created": "10 mins ago"},
    {"ticket_id": "TCK-502", "customer": "Ananya Sharma", "topic": "Bidding Price Verification", "status": "Resolved", "priority": "Low", "created": "2 hours ago"},
    {"ticket_id": "TCK-503", "customer": "David Kim", "topic": "Refurbishment Warranty Claim", "status": "In Progress (Assigned)", "priority": "High", "created": "1 day ago"}
]

# Tickets that consumers raise with the platform team (not their own customers' tickets).
# status: Open, In progress or Resolved. Hours are None until that step has happened.
PLATFORM_TICKETS = [
    {"ticket_id": "PT-201", "tenant_id": "t-001", "consumer": "GreenCycle Refurbishers", "subject": "Photo grading results look inconsistent", "priority": "High", "status": "Open", "opened": "2026-10-06", "first_response_hours": 1.5, "resolution_hours": None},
    {"ticket_id": "PT-204", "tenant_id": "t-001", "consumer": "GreenCycle Refurbishers", "subject": "Invoice shows the wrong API fee", "priority": "Low", "status": "Resolved", "opened": "2026-10-02", "first_response_hours": 4.0, "resolution_hours": 26.0},
    {"ticket_id": "PT-208", "tenant_id": "t-001", "consumer": "GreenCycle Refurbishers", "subject": "Question about reorder point settings", "priority": "Normal", "status": "Open", "opened": "2026-10-07", "first_response_hours": None, "resolution_hours": None},
]

# Queries: general questions anyone can send from the home page (name, email, mobile number and the question).
# The team answers by email or phone. This is not the same as a ticket, which a consumer raises about its own account.
# status: New, In conversation or Closed. first_response_hours is None until the team has replied.
QUERY_STATUSES = ("New", "In conversation", "Closed")
QUERIES = [
    {"query_id": "Q-312", "name": "Priya Nair", "email": "priya.nair@mailbox.example", "mobile": "+91 90000 00112", "message": "Can your platform manage stock across several warehouses for a refurbished electronics store?", "received": "2026-10-07", "status": "New", "first_response_hours": None},
    {"query_id": "Q-311", "name": "Rahul Verma", "email": "rahul.verma@mailbox.example", "mobile": "+91 90000 00111", "message": "Is there an integration with Shopify?", "received": "2026-10-07", "status": "New", "first_response_hours": None},
    {"query_id": "Q-310", "name": "Hannah Fischer", "email": "hannah.fischer@mailbox.example", "mobile": "+49 150 0000 0110", "message": "Do you offer a free trial for small retailers?", "received": "2026-10-06", "status": "New", "first_response_hours": None},
    {"query_id": "Q-309", "name": "Daniel Okafor", "email": "daniel.okafor@mailbox.example", "mobile": "+234 800 000 0109", "message": "I would like a demo of the return grading AI for my repair shop.", "received": "2026-10-05", "status": "In conversation", "first_response_hours": 3.0},
    {"query_id": "Q-308", "name": "Liam Carter", "email": "liam.carter@mailbox.example", "mobile": "+1 555 010 0108", "message": "We need help moving 4,000 products onto the catalog in one go.", "received": "2026-10-03", "status": "In conversation", "first_response_hours": 1.8},
    {"query_id": "Q-307", "name": "Aisha Khan", "email": "aisha.khan@mailbox.example", "mobile": "+971 50 000 0107", "message": "Can the shipment tracking cover cross-border returns?", "received": "2026-09-30", "status": "In conversation", "first_response_hours": 2.4},
    {"query_id": "Q-306", "name": "Mei Tanaka", "email": "mei.tanaka@mailbox.example", "mobile": "+81 90 0000 0106", "message": "What are the pricing options for a small retailer?", "received": "2026-09-27", "status": "Closed", "first_response_hours": 1.5},
    {"query_id": "Q-305", "name": "Sofia Alvarez", "email": "sofia.alvarez@mailbox.example", "mobile": "+34 600 000 105", "message": "How do I become a platform consumer?", "received": "2026-09-24", "status": "Closed", "first_response_hours": 2.2},
    {"query_id": "Q-304", "name": "Omar Haddad", "email": "omar.haddad@mailbox.example", "mobile": "+962 7 0000 0104", "message": "Does the bidding feature work with several sellers at once?", "received": "2026-09-20", "status": "Closed", "first_response_hours": 0.9},
    {"query_id": "Q-303", "name": "Chloe Martin", "email": "chloe.martin@mailbox.example", "mobile": "+33 6 00 00 01 03", "message": "Which countries do you support?", "received": "2026-09-17", "status": "Closed", "first_response_hours": 4.1},
    {"query_id": "Q-302", "name": "Arjun Mehta", "email": "arjun.mehta@mailbox.example", "mobile": "+91 90000 00102", "message": "Can the AI assistant answer in Hindi?", "received": "2026-09-14", "status": "Closed", "first_response_hours": 1.2},
    {"query_id": "Q-301", "name": "Grace Lee", "email": "grace.lee@mailbox.example", "mobile": "+65 8000 0101", "message": "Is my data kept private from other consumers?", "received": "2026-09-10", "status": "Closed", "first_response_hours": 2.0},
]

class FirestoreSaaS:
    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def list_platform_tickets(self) -> List[Dict[str, Any]]:
        return PLATFORM_TICKETS

    def list_queries(self) -> List[Dict[str, Any]]:
        return QUERIES

    def add_query(self, name: str, email: str, mobile: str, message: str) -> Dict[str, Any]:
        """Keep a new query from the home page; the team will reply by email or phone."""
        query_id = f"Q-{int(QUERIES[0]['query_id'].split('-')[1]) + 1}" if QUERIES else "Q-301"
        query = {"query_id": query_id, "name": name, "email": email, "mobile": mobile, "message": message,
                 "received": datetime.date.today().isoformat(), "status": "New", "first_response_hours": None}
        QUERIES.insert(0, query)
        return query

    def update_query(self, query_id: str, status: str) -> Optional[Dict[str, Any]]:
        query = next((q for q in QUERIES if q["query_id"] == query_id), None)
        if query is None or status not in QUERY_STATUSES:
            return None
        query["status"] = status
        # the first reply is the move off New
        if status != "New" and query["first_response_hours"] is None:
            query["first_response_hours"] = 1.0
        return query

    def list_tickets(self) -> List[Dict[str, Any]]:
        return TICKETS

firestore_saas = FirestoreSaaS()
