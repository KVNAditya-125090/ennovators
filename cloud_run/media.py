"""
Cloud Run - product photos and videos.
A consumer's team uploads pictures and videos for a product, and the same files show on the Customer storefront.

    POST /api/v1/consumer/media?filename=...   the file itself as the request body (not a form), with its Content-Type
    GET  /api/v1/media/{tenant_id}/{file}      anyone may view a stored file (customers see product media)

Who may upload: a named person of the workspace whose role allows adding or editing a product, in a workspace the Owner
opted into one of those two endpoints. The file's real type is read from its first bytes, never from the name or the
Content-Type the browser sent, so a page or script cannot be stored as a picture.
Files are kept in a private Cloud Storage bucket (cloud_storage/media_store.py) and served through this API. Cloud Run takes
requests up to 32 MB, so videos are limited to 30 MB; larger ones need a signed upload address straight to the bucket.
"""

import os
import re
import uuid
from typing import Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import Response

from cloud_sql.services.maas import cloud_sql_maas
from cloud_sql.services.maas.endpoints import endpoint_registry
from cloud_run.access import allowed_paths
from cloud_storage import media_store

router = APIRouter(tags=["Media"])

MAX_IMAGE = 10 * 1024 * 1024
MAX_VIDEO = 30 * 1024 * 1024
PRODUCT_PATHS = ("/paas/catalog/product/create/v1", "/paas/catalog/product/update/v1")
FILE_NAME = re.compile(r"^[0-9a-f]{32}\.(jpg|png|gif|webp|mp4|webm)$")
TYPES = {"jpg": ("image", "image/jpeg"), "png": ("image", "image/png"), "gif": ("image", "image/gif"), "webp": ("image", "image/webp"),
         "mp4": ("video", "video/mp4"), "webm": ("video", "video/webm")}

def _sniff(head: bytes) -> Optional[str]:
    """The file's real type from its first bytes: jpg, png, gif, webp, mp4 (also .mov) or webm. None for anything else."""
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[4:8] == b"ftyp":
        return "mp4"
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"
    return None

def _refuse(status: int, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": "media_refused", "message": message})

@router.post("/api/v1/consumer/media", status_code=201)
async def upload_media(request: Request, filename: str = "", x_tenant_id: Optional[str] = Header(None), x_user_email: Optional[str] = Header(None)) -> Dict[str, object]:
    from urllib.parse import unquote
    tenant = cloud_sql_maas.get_tenant(x_tenant_id) if x_tenant_id else None
    if tenant is None:
        raise _refuse(401, "Say which workspace is uploading with the X-Tenant-Id header.")
    email = unquote(x_user_email) if x_user_email else None
    if not email:
        raise _refuse(401, "Say who is uploading with the X-User-Email header.")
    opted = endpoint_registry.enabled_paths(x_tenant_id)
    allowed = allowed_paths(email, tenant["name"])  # None: the Root, no limit; an empty set: not one of this workspace
    usable = [p for p in PRODUCT_PATHS if p in opted and (allowed is None or p in allowed)]
    if not usable:
        raise _refuse(403, "Your workspace or role is not allowed to add or edit products, so it cannot upload product media.")
    declared = int(request.headers.get("content-length") or 0)
    if declared > MAX_VIDEO:
        raise _refuse(413, "That file is too large. Videos up to 30 MB, pictures up to 10 MB.")
    data = await request.body()
    if not data:
        raise _refuse(400, "The file is empty.")
    kind_ext = _sniff(data[:16])
    if kind_ext is None:
        raise _refuse(415, "Only JPG, PNG, WebP or GIF pictures and MP4 or WebM videos can be uploaded.")
    kind, content_type = TYPES[kind_ext]
    if len(data) > (MAX_IMAGE if kind == "image" else MAX_VIDEO):
        raise _refuse(413, "That picture is over 10 MB." if kind == "image" else "That video is over 30 MB.")
    name = f"{uuid.uuid4().hex}.{kind_ext}"
    media_store.put(x_tenant_id, name, data, content_type)
    endpoint_registry.record_audit(x_tenant_id, "/media/upload", "POST", 201, "ok")
    # absolute, so the site (a different address) can load it
    return {"url": f"{os.environ.get('PUBLIC_API_URL', '').rstrip('/')}/api/v1/media/{x_tenant_id}/{name}", "kind": kind, "content_type": content_type, "size": len(data), "name": filename[:120]}

@router.get("/api/v1/media/{tenant_id}/{file}")
def read_media(tenant_id: str, file: str):
    if not FILE_NAME.match(file) or not re.match(r"^[A-Za-z0-9_-]{1,40}$", tenant_id):
        raise HTTPException(status_code=404, detail="Not found")
    found = media_store.get(tenant_id, file)
    if found is None:
        raise HTTPException(status_code=404, detail="Not found")
    return Response(content=found[0], media_type=TYPES[file.rsplit(".", 1)[1]][1],
                        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "public, max-age=3600", "Content-Disposition": "inline"})
