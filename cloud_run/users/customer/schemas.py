"""
Customer Router - utilizes the services via the consumer (storefront, support, AI assistant). - request/response schemas (Pydantic models).
"""

from pydantic import BaseModel, Field

class QueryIn(BaseModel):
    """A query from the home page: who is asking, how to reach them, and the question."""
    name: str = Field(..., min_length=2, max_length=80)
    email: str = Field(..., max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
    mobile: str = Field(..., max_length=20, pattern=r"^\+?[0-9][0-9 ()-]{6,18}[0-9]$")
    message: str = Field(..., min_length=5, max_length=2000)
