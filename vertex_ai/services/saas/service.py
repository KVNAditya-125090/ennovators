"""
Vertex AI - SaaS (Support as a Service)
Gemini Flash return-photo condition grading (mock provider, keyless mode).
"""

from typing import Dict, Any, Optional

from vertex_ai import gemini

class VertexAISaaS:
    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def evaluate_return_photo(self, item_id: str, image_url: str = None, image: Optional[bytes] = None, mime: str = "image/jpeg",
                              item_name: str = "") -> Dict[str, Any]:
        """Grades a returned item from its photo with Gemini. Without a photo, or when Gemini cannot be reached, nothing is graded."""
        result = gemini.grade_photo(image, mime, item_name) if image else None
        if result is None:
            return {"item_id": item_id, "ai_evaluated_grade": None, "predicted_recovery_percentage": None, "recommended_channel": None,
                    "carbon_saved_kg": None, "defects": [],
                    "reasoning": "Send a photo of the item to have it graded." if not image else "The photo could not be graded just now. Please try again."}
        return {"item_id": item_id, "ai_evaluated_grade": f"Grade {result['grade']}", "predicted_recovery_percentage": result["recovery_percentage"],
                "recommended_channel": result["recommended_channel"], "carbon_saved_kg": None, "defects": result["defects"],
                "reasoning": result["reasoning"], "source": "Gemini"}

vertex_saas = VertexAISaaS()
