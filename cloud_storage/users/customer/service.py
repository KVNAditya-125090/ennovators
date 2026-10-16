"""
Cloud Storage - Customer
What the Customer uses: uploading return photos.
"""

from typing import Dict, Any
from cloud_storage.services.saas import cloud_storage_saas

def create_upload_url(item_id: str, content_type: str = "image/jpeg") -> Dict[str, Any]:
    return cloud_storage_saas.create_upload_url(item_id, content_type)
