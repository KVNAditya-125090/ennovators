"""
Cloud Run - Owner - request/response schemas.
"""

from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field

class QueryUpdate(BaseModel):
    """Move a query from the home page along: New, In conversation or Closed."""
    status: Literal["New", "In conversation", "Closed"]

class ApiToggle(BaseModel):
    enabled: bool

class ApiSettings(BaseModel):
    """Changes to one API's pricing and quota for one consumer. Send only what changed, or reset to the defaults."""
    monthly_fee_usd: Optional[float] = Field(None, ge=0, le=10000)
    price_per_1k_requests_usd: Optional[float] = Field(None, ge=0, le=1000)
    request_quota: Optional[int] = Field(None, ge=0, le=1_000_000_000)
    limits: Optional[Dict[str, int]] = None  # the limits that belong to this API, by key
    reset: bool = False
