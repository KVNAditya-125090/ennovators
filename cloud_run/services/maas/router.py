"""
Management as a Service (MaaS) Router
Handles role access, tenant configuration, system health, and budget tracking.
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Dict, Any, List, Optional
from urllib.parse import unquote
from cloud_sql.services.maas import cloud_sql_maas
from bigquery.services.maas import bigquery_maas
from cloud_run import auth
from cloud_run.access import is_owner
from cloud_run.services.maas.schemas import ForgotRequest, InviteAccept, LoginRequest, PasswordChange, Preferences, ResetRequest
from cloud_sql.services.maas.mailflows import mail_flows, mailbox_open

router = APIRouter(prefix="/api/v1/maas", tags=["Management as a Service (MaaS)"])

def owner_only(x_user_email: Optional[str] = Header(None)) -> None:
    """For the routes that list every consumer or user, or show money: a signed-in Owner only."""
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Sign in as an Owner to use this.")
    if not is_owner(unquote(x_user_email)):
        raise HTTPException(status_code=403, detail="Only the Owner can use this.")

@router.get("/health")
def get_system_health() -> Dict[str, Any]:
    return {
        "status": "Healthy",
        "service": "Lakshmi Core API",
        "mode": "Preview",
        "components": {
            "API": "Active",
            "Sign-in": "Email and password",
            "AI": "Mock",
            "Database": "Cloud SQL"
        }
    }

@router.get("/tenants", dependencies=[Depends(owner_only)])
def get_tenants() -> List[Dict[str, Any]]:
    return cloud_sql_maas.list_tenants()

@router.get("/users", dependencies=[Depends(owner_only)])
def get_users() -> List[Dict[str, Any]]:
    return cloud_sql_maas.list_users()

@router.get("/budget-status", dependencies=[Depends(owner_only)])
def get_budget_status() -> Dict[str, Any]:
    return bigquery_maas.get_budget_status()

@router.post("/auth/login")
def login(credentials: LoginRequest) -> Dict[str, Any]:
    """Single sign-in: the account decides the role, and the role decides the portal."""
    user = cloud_sql_maas.authenticate(credentials.email, credentials.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"user": user, "session": auth.issue_token({**user, "role": user["role"]})}

@router.get("/auth/preferences")
def read_preferences(x_user_email: Optional[str] = Header(None)) -> Dict[str, Any]:
    """The signed-in person's language and assistant modes."""
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Sign in first.")
    return cloud_sql_maas.get_preferences(unquote(x_user_email))

@router.put("/auth/preferences")
def save_preferences(prefs: Preferences, x_user_email: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Sign in first.")
    try:
        return cloud_sql_maas.set_preferences(unquote(x_user_email), prefs.language, prefs.modes)
    except ValueError as problem:
        raise HTTPException(status_code=422, detail=str(problem))

@router.post("/auth/password")
def change_password(change: PasswordChange, x_user_email: Optional[str] = Header(None)) -> Dict[str, Any]:
    """The signed-in person sets a new password. Needs the current one."""
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Sign in first.")
    try:
        done = cloud_sql_maas.change_password(unquote(x_user_email), change.current_password, change.new_password)
    except ValueError as problem:
        raise HTTPException(status_code=422, detail=str(problem))
    if not done:
        raise HTTPException(status_code=401, detail="The current password is not right.")
    return {"status": "changed"}

# ---- mails with a link: password reset and staff invite. The "mail" lands in the in-app mailbox (see cloud_sql/services/maas/mailflows.py) ----
@router.post("/auth/password/forgot")
def forgot_password(body: ForgotRequest) -> Dict[str, Any]:
    """Asks for a reset link. The answer is the same whether or not the address has an account."""
    mail_flows.request_reset(body.email)
    return {"status": "requested", "message": "If that address has an account, a reset link is in its mailbox."}

@router.post("/auth/password/reset")
def reset_password(body: ResetRequest) -> Dict[str, Any]:
    try:
        email = mail_flows.reset_password(body.token, body.new_password)
    except ValueError as problem:
        raise HTTPException(status_code=422, detail=str(problem))
    return {"status": "changed", "email": email}

@router.get("/auth/invite")
def read_invite(token: str) -> Dict[str, Any]:
    try:
        info = mail_flows.read_invite(token)
    except ValueError as problem:
        raise HTTPException(status_code=422, detail=str(problem))
    return {"mail": info["mail"], "role": info["role"], "workspace": info["workspace"]}

@router.post("/auth/invite/accept")
def accept_invite(body: InviteAccept) -> Dict[str, Any]:
    try:
        return {"status": "joined", **mail_flows.accept_invite(body.token, body.name, body.password)}
    except ValueError as problem:
        raise HTTPException(status_code=422, detail=str(problem))

@router.get("/auth/mailbox")
def read_mailbox(email: str) -> Dict[str, Any]:
    """The demo mailbox: what the app has "sent" to an address. Only when DEMO_MAILBOX=on."""
    if not mailbox_open():
        raise HTTPException(status_code=404, detail="The demo mailbox is switched off.")
    return {"email": email.strip().lower(), "mails": mail_flows.inbox(email)}
