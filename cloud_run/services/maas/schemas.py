"""
Cloud Run - MaaS (Management as a Service) - request/response schemas.
"""

from typing import Dict

from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class Preferences(BaseModel):
    language: str
    modes: Dict[str, bool] = {}

class ForgotRequest(BaseModel):
    email: str

class ResetRequest(BaseModel):
    token: str
    new_password: str

class InviteAccept(BaseModel):
    token: str
    name: str
    password: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
