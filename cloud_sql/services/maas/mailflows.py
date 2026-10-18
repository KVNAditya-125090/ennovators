"""
Cloud SQL - the demo's in-app mailbox, and the mails that carry a working link: password reset and staff invite.
Nothing leaves the system: a "sent" mail is a row in the mailbox table, and the link in it opens a page of the app.

Settings: APP_URL (where the links point, default the Firebase site), DEMO_MAILBOX=on (lets anyone read a mailbox by address;
leave it unset anywhere real, because the links in a mail can take over an account).
"""

import hashlib
import os
from typing import Any, Dict, List, Optional

from cloud_run import auth
from cloud_sql import db
from cloud_sql.services.maas.roles import roles as role_store
from cloud_sql.services.maas.service import cloud_sql_maas

RESET_HOURS = 1
INVITE_HOURS = 72

def app_url() -> str:
    return os.environ.get("APP_URL", "https://agent-lakshmi.web.app").rstrip("/")

def mailbox_open() -> bool:
    return os.environ.get("DEMO_MAILBOX", "").strip().lower() in ("on", "1", "true", "yes")

def _stamp(password_hash: str) -> str:
    """Changes when the password changes, so a reset link works once."""
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]

class MailFlows:
    def send(self, to_email: str, kind: str, subject: str, body: str, link: Optional[str] = None) -> None:
        db.run("INSERT INTO mailbox (to_email, kind, subject, body, link) VALUES (:to, :kind, :subject, :body, :link)",
               to=to_email.strip().lower(), kind=kind, subject=subject, body=body, link=link)

    def inbox(self, email: str, limit: int = 50) -> List[Dict[str, Any]]:
        return db.rows("""SELECT id, to_char(at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI') AS at, kind, subject, body, link
                          FROM mailbox WHERE lower(to_email) = :e ORDER BY id DESC LIMIT :n""", e=email.strip().lower(), n=limit)

    # ---- password reset ----
    def request_reset(self, email: str) -> None:
        """Mails a reset link when the address has an account. The caller answers the same way either way."""
        email = email.strip().lower()
        account = db.one("SELECT password_hash, active FROM accounts WHERE email = :e", e=email)
        if account is None or not account["active"]:
            return
        token = auth.issue_link_token("reset", {"mail": email, "stamp": _stamp(account["password_hash"])}, RESET_HOURS)
        link = f"{app_url()}/reset-password?token={token}"
        self.send(email, "password-reset", "Reset your Lakshmi password",
                  f"Someone asked to reset the password for {email}. Use the link within {RESET_HOURS} hour to choose a new one. "
                  "If this was not you, ignore this mail and nothing changes.", link)

    def reset_password(self, token: str, new_password: str) -> str:
        """Sets the new password and returns the account's email. Raises ValueError for a bad or used link or a weak password."""
        claims = auth.verify_link_token(token, "reset")
        if not claims:
            raise ValueError("This reset link is not valid or has expired. Ask for a new one.")
        problem = auth.password_problem(new_password)
        if problem:
            raise ValueError(problem)
        email = claims["mail"]
        account = db.one("SELECT password_hash FROM accounts WHERE email = :e", e=email)
        if account is None or _stamp(account["password_hash"]) != claims.get("stamp"):
            raise ValueError("This reset link has already been used. Ask for a new one.")
        db.run("""UPDATE accounts SET password_hash = :h, must_change_password = false, failed_attempts = 0, locked_until = NULL
                  WHERE email = :e""", h=auth.hash_password(new_password), e=email)
        self.send(email, "password-changed", "Your Lakshmi password was changed",
                  f"The password for {email} was just changed. If this was not you, ask your workspace administrator.")
        return email

    # ---- staff invite ----
    def send_invite(self, tenant_id: str, role_id: str, mail: str, inviter: Optional[str]) -> None:
        role = role_store.get_role(tenant_id, role_id)
        tenant = cloud_sql_maas.get_tenant(tenant_id) or {}
        token = auth.issue_link_token("invite", {"mail": mail.strip().lower(), "tenant": tenant_id, "role_id": role_id}, INVITE_HOURS)
        link = f"{app_url()}/accept-invite?token={token}"
        self.send(mail, "staff-invite", f"You are invited to {tenant.get('name', 'a workspace')} as {role['name']}",
                  f"{inviter or 'The workspace owner'} gave you the {role['name']} role at {tenant.get('name', 'their workspace')}. "
                  f"Use the link within {INVITE_HOURS // 24} days to set your name and password and sign in.", link)

    def read_invite(self, token: str) -> Dict[str, Any]:
        claims = auth.verify_link_token(token, "invite")
        if not claims:
            raise ValueError("This invite is not valid or has expired. Ask your administrator to send a new one.")
        mail = db.one("SELECT status FROM role_mails WHERE role_id = CAST(:r AS uuid) AND mail = :m", r=claims["role_id"], m=claims["mail"])
        if mail is None:
            raise ValueError("This invite was withdrawn.")
        if cloud_sql_maas.find_user(claims["mail"]):
            raise ValueError("This invite has already been used. Sign in instead.")
        role = role_store.get_role(claims["tenant"], claims["role_id"])
        tenant = cloud_sql_maas.get_tenant(claims["tenant"]) or {}
        return {"mail": claims["mail"], "role": role["name"], "workspace": tenant.get("name", ""), "claims": claims}

    def accept_invite(self, token: str, name: str, password: str) -> Dict[str, Any]:
        info = self.read_invite(token)
        claims = info["claims"]
        name = (name or "").strip()
        if not name:
            raise ValueError("Enter your name.")
        cloud_sql_maas.create_account(name, claims["mail"], f"Consumer / {info['role']}", "Consumer", password, tenant_id=claims["tenant"])
        db.run("UPDATE role_mails SET status = 'active' WHERE role_id = CAST(:r AS uuid) AND mail = :m", r=claims["role_id"], m=claims["mail"])
        role_store.log_mail(claims["tenant"], "invite-accepted", claims["role_id"], claims["mail"], f"{claims['mail']} accepted the invite and joined as {info['role']}.")
        return {"email": claims["mail"], "role": info["role"], "workspace": info["workspace"]}

mail_flows = MailFlows()
