"""
Support as a Service (SaaS) Router
Handles queries, after-sales support, photo-based return triage, and AI assistant chat.
"""

from fastapi import APIRouter, Body
from typing import Dict, Any, List
from vertex_ai.services.saas import vertex_saas
from firestore.services.saas import firestore_saas
from cloud_storage.services.saas import cloud_storage_saas

router = APIRouter(prefix="/api/v1/saas", tags=["Support as a Service (SaaS)"])

@router.post("/chat")
def chat_with_assistant(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user_msg = data.get("message", "")
    context = data.get("context", {})
    return vertex_saas.chat_assistant(user_msg, context)

@router.post("/returns/triage")
def triage_return_request(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    item_id = data.get("item_id", "ITEM-DEFAULT")
    image_url = data.get("image_url", "")
    return vertex_saas.evaluate_return_photo(item_id, image_url)

@router.post("/returns/upload-url")
def create_return_photo_upload_url(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    item_id = data.get("item_id", "ITEM-DEFAULT")
    return cloud_storage_saas.create_upload_url(item_id, data.get("content_type", "image/jpeg"))

@router.get("/tickets")
def get_support_tickets() -> List[Dict[str, Any]]:
    return firestore_saas.list_tickets()
