"""
Cloud Run - sign-in.
Passwords are stored only as a salted scrypt hash. A successful sign-in returns a signed token (HS256, 8 hours) that
names the person. The identity middleware reads that token on every call and sets the X-User-Email header from it, after
removing any X-User-Email the caller sent, so the rest of the code can trust the header and nobody can forge it.

This is the stand-in for Firebase Authentication: when that arrives, only issue_token and verify_token change.

Settings: JWT_SECRET (required; on Cloud Run it comes from Secret Manager).
"""

import base64
import hashlib
import hmac
import os
import secrets
import time
from typing import Any, Dict, Optional
from urllib.parse import quote

import jwt

TOKEN_HOURS = 8
ISSUER = "lakshmi"
MIN_PASSWORD_LENGTH = 10
_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2 ** 14, 8, 1

def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32)
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${_b64(salt)}${_b64(digest)}"

def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = base64.b64decode(digest)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

# A hash to check against when the email is unknown, so a miss takes as long as a hit
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))

def password_problem(password: str) -> Optional[str]:
    """Why a new password is not acceptable, or None when it is."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Use at least {MIN_PASSWORD_LENGTH} characters."
    if password.lower() == password or password.upper() == password or not any(c.isdigit() for c in password):
        return "Mix upper and lower case letters and at least one number."
    return None

def _secret() -> str:
    key = os.environ.get("JWT_SECRET")
    if not key:
        raise RuntimeError("JWT_SECRET is not set: sign-in is not configured")
    return key

def issue_token(user: Dict[str, Any]) -> Dict[str, Any]:
    now = int(time.time())
    claims = {"iss": ISSUER, "sub": user["email"].lower(), "uid": user["user_id"], "role": user["role"],
              "tenant": user.get("tenant"), "iat": now, "exp": now + TOKEN_HOURS * 3600}
    return {"access_token": jwt.encode(claims, _secret(), algorithm="HS256"), "token_type": "Bearer", "expires_in": TOKEN_HOURS * 3600}

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, _secret(), algorithms=["HS256"], issuer=ISSUER, options={"require": ["exp", "sub"]})
    except (jwt.PyJWTError, RuntimeError):
        return None

def issue_link_token(purpose: str, claims: Dict[str, Any], hours: int) -> str:
    """A signed token for a link in a mail (a password reset or an invite). The purpose keeps one kind from working as another."""
    now = int(time.time())
    return jwt.encode({**claims, "iss": ISSUER, "purpose": purpose, "iat": now, "exp": now + hours * 3600}, _secret(), algorithm="HS256")

def verify_link_token(token: str, purpose: str) -> Optional[Dict[str, Any]]:
    claims = verify_token_any(token)
    return claims if claims and claims.get("purpose") == purpose else None

def verify_token_any(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, _secret(), algorithms=["HS256"], issuer=ISSUER, options={"require": ["exp"]})
    except (jwt.PyJWTError, RuntimeError):
        return None

class IdentityMiddleware:
    """Replaces whatever X-User-Email the caller sent with the one in their verified token (or none)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            token = None
            kept = []
            for key, value in scope["headers"]:
                if key == b"x-user-email":
                    continue
                if key == b"authorization" and value[:7].lower() == b"bearer ":
                    token = value[7:].decode("latin-1").strip()
                kept.append((key, value))
            claims = verify_token(token) if token else None
            if claims:
                kept.append((b"x-user-email", quote(claims["sub"]).encode("ascii")))
            scope = {**scope, "headers": kept}
        await self.app(scope, receive, send)
