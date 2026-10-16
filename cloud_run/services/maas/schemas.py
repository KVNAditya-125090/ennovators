"""
Cloud Run - MaaS (Management as a Service) - request/response schemas.
"""

from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str
