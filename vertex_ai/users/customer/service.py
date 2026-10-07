"""
Vertex AI - Customer
What the Customer uses: the AI shopping assistant and photo-based return grading.
"""

from typing import Dict, Any
from vertex_ai.services.saas import vertex_saas

def chat(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    return vertex_saas.chat_assistant(message, context)

def triage_return(item_id: str, image_url: str = None) -> Dict[str, Any]:
    return vertex_saas.evaluate_return_photo(item_id, image_url)
