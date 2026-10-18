"""
Cloud SQL (PostgreSQL) - MaaS (Management as a Service)
Relational, multi-tenant system of record: tenants, users and their sign-in accounts.
Every function returns the same plain dicts the rest of the code already used.
"""

import json
from typing import Dict, Any, List, Optional

from cloud_sql import db
from cloud_run import auth

# Languages a person can choose, and the four ways to talk to an assistant:
# t2t text in, text out   t2s text in, spoken answer   s2t spoken question, text answer   s2s spoken both ways
LANGUAGES = ("en", "hi", "te", "ta", "kn", "mr", "bn", "gu", "ml")
MODES = ("t2t", "t2s", "s2t", "s2s")
DEFAULT_PREFERENCES = {"language": "en", "modes": {"t2t": True, "t2s": False, "s2t": False, "s2s": False}}

PLATFORM = "Lakshmi"        # the "tenant" shown for Owner users, who belong to the platform and not to a consumer
MAX_FAILED_SIGN_INS = 5
LOCK_MINUTES = 15

_TENANT = """SELECT t.tenant_id::text AS tenant_id, t.name, t.type, t.status,
                    (SELECT count(*) FROM users u WHERE u.tenant_id = t.tenant_id)::int AS users_count
             FROM tenants t"""
_USER = """SELECT u.user_id::text AS user_id, u.name, u.email, u.role, coalesce(t.name, :platform) AS tenant, u.tenant_id::text AS tenant_id
           FROM users u LEFT JOIN tenants t ON t.tenant_id = u.tenant_id"""

class CloudSQLMaaS:
    def __init__(self):
        self.provider_status = "Cloud SQL (PostgreSQL)"

    # ---- tenants and users ----
    def list_tenants(self) -> List[Dict[str, Any]]:
        return db.rows(_TENANT + " ORDER BY t.created_at")

    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        return db.one(_TENANT + " WHERE t.tenant_id = CAST(:id AS uuid)", id=tenant_id)

    def get_tenant_by_name(self, tenant_name: str) -> Optional[Dict[str, Any]]:
        return db.one(_TENANT + " WHERE t.name = :name", name=tenant_name)

    def list_users(self) -> List[Dict[str, Any]]:
        return db.rows(_USER + " ORDER BY u.created_at", platform=PLATFORM)

    def find_user(self, email: str) -> Optional[Dict[str, Any]]:
        return db.one(_USER + " WHERE lower(u.email) = :email", email=email.strip().lower(), platform=PLATFORM)

    def list_members(self, tenant_name: str) -> List[Dict[str, Any]]:
        return db.rows(_USER + " WHERE t.name = :name ORDER BY u.created_at", name=tenant_name, platform=PLATFORM)

    def get_workspace(self, tenant_name: str) -> Optional[Dict[str, Any]]:
        """A tenant workspace with its team, for the consumers who run it."""
        tenant = self.get_tenant_by_name(tenant_name)
        if tenant is None:
            return None
        return {"tenant": tenant, "members": self.list_members(tenant_name)}

    def get_profile(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        row = db.one("SELECT profile FROM tenants WHERE tenant_id = CAST(:id AS uuid)", id=tenant_id)
        if row is None or not row["profile"]:
            return None
        profile = row["profile"] if isinstance(row["profile"], dict) else json.loads(row["profile"])
        return {group: dict(values) for group, values in profile.items()}

    # ---- personal settings: language and how to talk to the assistants ----
    def get_preferences(self, email: str) -> Dict[str, Any]:
        row = db.one("SELECT preferences FROM users WHERE lower(email) = :e", e=email.strip().lower())
        saved = {} if row is None else (row["preferences"] if isinstance(row["preferences"], dict) else json.loads(row["preferences"] or "{}"))
        return {"language": saved.get("language", "en"), "modes": {**DEFAULT_PREFERENCES["modes"], **saved.get("modes", {})}}

    def set_preferences(self, email: str, language: str, modes: Dict[str, bool]) -> Dict[str, Any]:
        """Saves a person's language and modes. Raises ValueError for a language or mode that does not exist."""
        if language not in LANGUAGES:
            raise ValueError("That language is not available.")
        unknown = set(modes) - set(MODES)
        if unknown:
            raise ValueError("Unknown mode: " + ", ".join(sorted(unknown)))
        clean = {m: bool(modes.get(m, DEFAULT_PREFERENCES["modes"][m])) for m in MODES}
        clean["t2t"] = True  # reading and typing always stays available
        db.run("UPDATE users SET preferences = CAST(:p AS jsonb) WHERE lower(email) = :e", p=json.dumps({"language": language, "modes": clean}), e=email.strip().lower())
        return {"language": language, "modes": clean}

    # ---- creating them ----
    def create_tenant(self, name: str, type_: str = "", profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from sqlalchemy import text
        with db.tx() as conn:  # a write needs a transaction: db.one and db.rows only read
            tenant_id = conn.execute(text("""INSERT INTO tenants (name, type, profile) VALUES (:name, :type, CAST(:profile AS jsonb))
                                             RETURNING tenant_id::text"""),
                                     {"name": name, "type": type_, "profile": json.dumps(profile or {})}).scalar()
        return self.get_tenant(tenant_id)

    def create_account(self, name: str, email: str, role: str, portal: str, password: str,
                       tenant_id: Optional[str] = None, must_change_password: bool = False) -> Dict[str, Any]:
        """Makes a user and the account they sign in with. Raises ValueError for a weak password or a used email."""
        problem = auth.password_problem(password)
        if problem:
            raise ValueError(problem)
        email = email.strip().lower()
        if self.find_user(email):
            raise ValueError(f"{email} already has an account")
        with db.tx() as conn:
            from sqlalchemy import text
            user_id = conn.execute(text("""INSERT INTO users (name, email, role, tenant_id)
                                           VALUES (:name, :email, :role, CAST(:tenant AS uuid)) RETURNING user_id::text"""),
                                   {"name": name, "email": email, "role": role, "tenant": tenant_id}).scalar()
            conn.execute(text("""INSERT INTO accounts (email, password_hash, user_id, portal, must_change_password)
                                 VALUES (:email, :hash, CAST(:uid AS uuid), :portal, :must)"""),
                         {"email": email, "hash": auth.hash_password(password), "uid": user_id, "portal": portal, "must": must_change_password})
        return self.find_user(email)

    # ---- signing in ----
    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """The signed-in user with the portal their account belongs to, or None. Five wrong passwords lock the account for 15 minutes."""
        email = email.strip().lower()
        account = db.one("""SELECT password_hash, portal, active, must_change_password, (locked_until IS NOT NULL AND locked_until > now()) AS locked
                            FROM accounts WHERE email = :email""", email=email)
        # always check a hash, so a wrong email takes as long as a wrong password
        ok = auth.verify_password(password, account["password_hash"] if account else auth.DUMMY_HASH)
        if account is None or not account["active"] or account["locked"]:
            return None
        if not ok:
            db.run("""UPDATE accounts SET failed_attempts = failed_attempts + 1,
                      locked_until = CASE WHEN failed_attempts + 1 >= :max THEN now() + make_interval(mins => :mins) ELSE locked_until END
                      WHERE email = :email""", email=email, max=MAX_FAILED_SIGN_INS, mins=LOCK_MINUTES)
            return None
        db.run("UPDATE accounts SET failed_attempts = 0, locked_until = NULL, last_login = now() WHERE email = :email", email=email)
        user = self.find_user(email)
        if user is None:
            return None
        return {"user_id": user["user_id"], "name": user["name"], "email": user["email"], "role": account["portal"],
                "tenant": user["tenant"], "must_change_password": account["must_change_password"], "preferences": self.get_preferences(email),
                # sub-role shown beside the portal: Owner (Manager / Developer / Operator), Consumer (as registered)
                "department": user["role"].partition(" / ")[2] or None}

    def change_password(self, email: str, current: str, new: str) -> bool:
        problem = auth.password_problem(new)
        if problem:
            raise ValueError(problem)
        if self.authenticate(email, current) is None:
            return False
        db.run("UPDATE accounts SET password_hash = :hash, must_change_password = false WHERE email = :email",
               hash=auth.hash_password(new), email=email.strip().lower())
        return True

cloud_sql_maas = CloudSQLMaaS()
