"""
Firestore - SaaS (Support as a Service)
Document collections: support tickets, and queries from the home page.
"""

import datetime
from typing import Dict, Any, List, Optional
from cloud_run.ids import new_id
from firestore import store


# Tickets that consumers raise with the platform team (not their own customers' tickets).
# status: Open, In progress or Resolved. Hours are None until that step has happened.

# Queries: general questions anyone can send from the home page (name, email, mobile number and the question).
# The team answers by email or phone. This is not the same as a ticket, which a consumer raises about its own account.
# status: New, In conversation or Closed. first_response_hours is None until the team has replied.
QUERY_STATUSES = ("New", "In conversation", "Closed")

class FirestoreSaaS:
    @staticmethod
    def _queries() -> List[Dict[str, Any]]:
        """Visitor queries from the home page belong to the platform, not to a consumer."""
        return store.rows("queries", "query_id", scope="global", newest_first=True)

    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def list_platform_tickets(self) -> List[Dict[str, Any]]:
        return store.rows("platform_tickets", "ticket_id", scope="global", newest_first=True)

    def list_queries(self) -> List[Dict[str, Any]]:
        return self._queries()

    def add_query(self, name: str, email: str, mobile: str, message: str) -> Dict[str, Any]:
        """Keep a new query from the home page; the team will reply by email or phone."""
        query_id = new_id()
        query = {"query_id": query_id, "name": name, "email": email, "mobile": mobile, "message": message,
                 "received": datetime.date.today().isoformat(), "status": "New", "first_response_hours": None}
        self._queries().insert(0, query)
        return query

    def update_query(self, query_id: str, status: str) -> Optional[Dict[str, Any]]:
        query = next((q for q in self._queries() if q["query_id"] == query_id), None)
        if query is None or status not in QUERY_STATUSES:
            return None
        query["status"] = status
        # the first reply is the move off New
        if status != "New" and query["first_response_hours"] is None:
            query["first_response_hours"] = 1.0
        return query

    def list_tickets(self) -> List[Dict[str, Any]]:
        return store.rows("storefront_tickets", "ticket_id", newest_first=True)

firestore_saas = FirestoreSaaS()
