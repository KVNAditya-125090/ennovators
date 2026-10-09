"""
Cloud Run - Owner - request/response schemas.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field

class QueryUpdate(BaseModel):
    """Move a query from the home page along: New, In conversation or Closed."""
    status: Literal["New", "In conversation", "Closed"]

class EndpointToggle(BaseModel):
    """Opt one endpoint of the catalog in or out for a consumer. The path has slashes, so it travels in the body."""
    path: str = Field(..., min_length=1, max_length=200)
    enabled: bool

class ServiceToggle(BaseModel):
    enabled: bool

class EndpointSettings(BaseModel):
    """One endpoint's rate limit and price for one consumer. Send only what changed, or reset all three to the defaults."""
    path: str = Field(..., min_length=1, max_length=200)
    rate_limit_per_min: Optional[int] = Field(None, ge=1, le=10000)
    monthly_fee_usd: Optional[float] = Field(None, ge=0, le=10000)
    price_per_1k_calls_usd: Optional[float] = Field(None, ge=0, le=1000)
    reset: bool = False
