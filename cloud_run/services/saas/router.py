"""
Support as a Service (SaaS) Router
Handles queries, after-sales support, photo-based return triage.
"""

from fastapi import APIRouter, Body, Header, HTTPException
from typing import Dict, Any, List, Optional
from urllib.parse import unquote
from firestore import store
from cloud_run.access import staff_tenant_id
from cloud_run.photos import decode_photo, take_turn
from vertex_ai.services.saas import vertex_saas
from firestore.services.saas import firestore_saas
from cloud_storage.services.saas import cloud_storage_saas

router = APIRouter(prefix="/api/v1/saas", tags=["Support as a Service (SaaS)"])

@router.post("/returns/triage")
def triage_return_request(data: Dict[str, Any] = Body(...), x_user_email: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Grades a returned item from a photo (image_base64: a JPEG, PNG or WebP, plain base64 or a data URL). Needs a signed-in person."""
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Sign in to grade a photo.")
    item_id = data.get("item_id") or "ITEM-DEFAULT"
    if not data.get("image_base64"):
        return vertex_saas.evaluate_return_photo(item_id, data.get("image_url", ""))
    try:
        image, mime = decode_photo(data["image_base64"])
        take_turn(unquote(x_user_email))
    except ValueError as problem:
        raise HTTPException(status_code=422, detail=str(problem))
    return vertex_saas.evaluate_return_photo(item_id, image=image, mime=mime, item_name=str(data.get("item_name", ""))[:80])

@router.post("/returns/upload-url")
def create_return_photo_upload_url(data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    item_id = data.get("item_id", "ITEM-DEFAULT")
    return cloud_storage_saas.create_upload_url(item_id, data.get("content_type", "image/jpeg"))

@router.get("/tickets")
def get_support_tickets(x_user_email: Optional[str] = Header(None)) -> List[Dict[str, Any]]:
    store.set_tenant(staff_tenant_id(unquote(x_user_email) if x_user_email else None))
    return firestore_saas.list_tickets()
