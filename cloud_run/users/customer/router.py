"""
Customer Router - utilizes the services via the consumer (storefront, support, AI assistant).
"""

from fastapi import APIRouter, Body
from cloud_run.users.customer.schemas import QueryIn
from typing import Dict, Any
from firestore.users import customer as firestore
from vertex_ai.users import customer as vertex_ai
from cloud_storage.users import customer as cloud_storage

router = APIRouter(prefix="/api/v1/customer", tags=["Customer"])

@router.get("/storefront")
def get_storefront() -> Dict[str, Any]:
    return {
        "products": firestore.browse_catalog(),
        "tickets": firestore.my_tickets()
    }

@router.post("/queries", status_code=201)
def send_query(query: QueryIn) -> Dict[str, Any]:
    """Anyone can ask a question from the home page. The team replies by email or phone."""
    saved = firestore.submit_query(query.name.strip(), query.email.strip(), query.mobile.strip(), query.message.strip())
    return {"query_id": saved["query_id"], "status": saved["status"]}

@router.post("/assistant")
def ask_assistant(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return vertex_ai.chat(data.get("message", ""), data.get("context", {}))

@router.post("/returns")
def start_return(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    item_id = data.get("item_id", "ITEM-DEFAULT")
    return {
        "upload": cloud_storage.create_upload_url(item_id, data.get("content_type", "image/jpeg")),
        "triage": vertex_ai.triage_return(item_id, data.get("image_url", ""))
    }
