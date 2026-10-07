"""
Support as a Service (SaaS) Router
Handles queries, after-sales support, photo-based return triage, and AI assistant chat.
"""

from fastapi import APIRouter, Body
from typing import Dict, Any, List
from services.vertex_mock import vertex_service

router = APIRouter(prefix="/api/v1/saas", tags=["Support as a Service (SaaS)"])

@router.post("/chat")
def chat_with_assistant(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user_msg = data.get("message", "")
    context = data.get("context", {})
    return vertex_service.chat_assistant(user_msg, context)

@router.post("/returns/triage")
def triage_return_request(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    item_id = data.get("item_id", "ITEM-DEFAULT")
    image_url = data.get("image_url", "")
    return vertex_service.evaluate_return_photo(item_id, image_url)

@router.get("/tickets")
def get_support_tickets() -> List[Dict[str, Any]]:
    return [
        {"ticket_id": "TCK-501", "customer": "Marcus Vance", "topic": "Return Photo Triage", "status": "AI Auto-Approved (Grade A)", "priority": "Normal", "created": "10 mins ago"},
        {"ticket_id": "TCK-502", "customer": "Ananya Sharma", "topic": "Bidding Price Verification", "status": "Resolved", "priority": "Low", "created": "2 hours ago"},
        {"ticket_id": "TCK-503", "customer": "David Kim", "topic": "Refurbishment Warranty Claim", "status": "In Progress (Assigned)", "priority": "High", "created": "1 day ago"}
    ]

