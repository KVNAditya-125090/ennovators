"""
Cloud Storage - product photos and videos.
Files live in a private bucket, one folder per consumer: {tenant id}/{file name}. The API is the only way in or out,
so it can check who may upload and what the file really is. The service account of the backend is the only account
with access to the bucket.

Settings: MEDIA_BUCKET (default lakshmi-media-ennovators).
"""

import logging
import os
import threading
from typing import Optional, Tuple

log = logging.getLogger("lakshmi.media")

_bucket = None
_lock = threading.Lock()

def bucket():
    global _bucket
    if _bucket is None:
        with _lock:
            if _bucket is None:
                from google.cloud import storage
                _bucket = storage.Client(project=os.environ.get("GCP_PROJECT", "ennovators")).bucket(os.environ.get("MEDIA_BUCKET", "lakshmi-media-ennovators"))
    return _bucket

def put(tenant_id: str, name: str, data: bytes, content_type: str) -> None:
    bucket().blob(f"{tenant_id}/{name}").upload_from_string(data, content_type=content_type)

def get(tenant_id: str, name: str) -> Optional[Tuple[bytes, str]]:
    """The file and its type, or None when it does not exist."""
    blob = bucket().blob(f"{tenant_id}/{name}")
    if not blob.exists():
        return None
    return blob.download_as_bytes(), blob.content_type or "application/octet-stream"

def delete(tenant_id: str, name: str) -> None:
    bucket().blob(f"{tenant_id}/{name}").delete()
