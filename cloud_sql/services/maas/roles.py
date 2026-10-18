"""
Cloud SQL (PostgreSQL) - MaaS roles.
A consumer's internal roles (for example IT, Marketing, Operation, Support), who holds each one, which endpoints each may
call, the mail log of role events, and the storefront template with how each role sees the workspace.
Everything is kept per consumer (tenant), so one consumer's roles never touch another's.
A missing record raises LookupError and a refused change raises ValueError; the gate turns them into 404 and 422.
"""

import json
import re
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text

from cloud_sql import db

EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

def _role(row: Dict[str, Any]) -> Dict[str, Any]:
    return {"role_id": row["role_id"], "name": row["name"], "description": row["description"], "active": row["active"]}

_ROLE = "SELECT role_id::text AS role_id, name, description, active FROM roles"

class RoleStore:
    # ---- roles ----
    def list_roles(self, tenant_id: str) -> List[Dict[str, Any]]:
        return [_role(r) for r in db.rows(_ROLE + " WHERE tenant_id = CAST(:t AS uuid) ORDER BY created_at, name", t=tenant_id)]

    def get_role(self, tenant_id: str, role_id: str) -> Dict[str, Any]:
        row = db.one(_ROLE + " WHERE tenant_id = CAST(:t AS uuid) AND role_id = CAST(:r AS uuid)", t=tenant_id, r=role_id)
        if row is None:
            raise LookupError(f"No record with role_id {role_id}")
        return _role(row)

    def create_role(self, tenant_id: str, name: str, description: Optional[str]) -> Dict[str, Any]:
        if db.one("SELECT 1 AS x FROM roles WHERE tenant_id = CAST(:t AS uuid) AND lower(name) = lower(:n)", t=tenant_id, n=name):
            raise ValueError(f"A role called {name} already exists")
        with db.tx() as conn:
            role_id = conn.execute(text("INSERT INTO roles (tenant_id, name, description) VALUES (CAST(:t AS uuid), :n, :d) RETURNING role_id::text"),
                                   {"t": tenant_id, "n": name, "d": description or ""}).scalar()
        return self.get_role(tenant_id, role_id)

    def update_role(self, tenant_id: str, role_id: str, name: Optional[str], description: Optional[str]) -> Dict[str, Any]:
        self.get_role(tenant_id, role_id)
        if name:
            db.run("UPDATE roles SET name = :n WHERE role_id = CAST(:r AS uuid)", n=name, r=role_id)
        if description is not None:
            db.run("UPDATE roles SET description = :d WHERE role_id = CAST(:r AS uuid)", d=description, r=role_id)
        return self.get_role(tenant_id, role_id)

    def deactivate_role(self, tenant_id: str, role_id: str) -> Dict[str, Any]:
        self.get_role(tenant_id, role_id)
        db.run("UPDATE roles SET active = false WHERE role_id = CAST(:r AS uuid)", r=role_id)
        return self.get_role(tenant_id, role_id)

    # ---- who holds each role ----
    def list_mails(self, tenant_id: str) -> List[Dict[str, Any]]:
        return db.rows("""SELECT m.role_id::text AS role_id, m.mail, m.status FROM role_mails m JOIN roles r ON r.role_id = m.role_id
                          WHERE r.tenant_id = CAST(:t AS uuid) ORDER BY r.created_at, m.mail""", t=tenant_id)

    def assign_mail(self, tenant_id: str, role_id: str, mail: str) -> Dict[str, Any]:
        role = self.get_role(tenant_id, role_id)
        if not role["active"]:
            raise ValueError(f"The {role['name']} role is inactive")
        mail = mail.strip().lower()
        if not EMAIL.fullmatch(mail):
            raise ValueError(f"{mail} is not a valid email address")
        if db.one("SELECT 1 AS x FROM role_mails WHERE role_id = CAST(:r AS uuid) AND mail = :m", r=role_id, m=mail):
            raise ValueError(f"{mail} already holds the {role['name']} role")
        db.run("INSERT INTO role_mails (role_id, mail, status) VALUES (CAST(:r AS uuid), :m, 'invited')", r=role_id, m=mail)
        return {"role_id": role_id, "mail": mail, "status": "invited"}

    def remove_mail(self, tenant_id: str, role_id: str, mail: str) -> Dict[str, Any]:
        self.get_role(tenant_id, role_id)
        mail = mail.strip().lower()
        row = db.one("SELECT status FROM role_mails WHERE role_id = CAST(:r AS uuid) AND mail = :m", r=role_id, m=mail)
        if row is None:
            raise LookupError(f"{mail} does not hold this role")
        db.run("DELETE FROM role_mails WHERE role_id = CAST(:r AS uuid) AND mail = :m", r=role_id, m=mail)
        return {"role_id": role_id, "mail": mail, "status": row["status"]}

    def held_roles(self, tenant_id: str, email: str) -> List[str]:
        """The ids of the active roles this person holds in this consumer."""
        return [r["role_id"] for r in db.rows("""SELECT r.role_id::text AS role_id FROM role_mails m JOIN roles r ON r.role_id = m.role_id
                                                 WHERE r.tenant_id = CAST(:t AS uuid) AND r.active AND m.mail = :m""", t=tenant_id, m=email.strip().lower())]

    # ---- what each role may call ----
    def permissions(self, tenant_id: str, role_id: str) -> List[str]:
        self.get_role(tenant_id, role_id)
        return [r["path"] for r in db.rows("SELECT path FROM role_permissions WHERE role_id = CAST(:r AS uuid) ORDER BY path", r=role_id)]

    def grant(self, tenant_id: str, role_id: str, path: str) -> None:
        role = self.get_role(tenant_id, role_id)
        if not role["active"]:
            raise ValueError(f"The {role['name']} role is inactive")
        db.run("INSERT INTO role_permissions (role_id, path) VALUES (CAST(:r AS uuid), :p) ON CONFLICT DO NOTHING", r=role_id, p=path)

    def grant_many(self, tenant_id: str, role_id: str, paths: List[str]) -> None:
        self.get_role(tenant_id, role_id)
        if paths:
            db.run("INSERT INTO role_permissions (role_id, path) SELECT CAST(:r AS uuid), unnest(CAST(:p AS text[])) ON CONFLICT DO NOTHING", r=role_id, p=sorted(paths))

    def revoke(self, tenant_id: str, role_id: str, path: str) -> None:
        self.get_role(tenant_id, role_id)
        db.run("DELETE FROM role_permissions WHERE role_id = CAST(:r AS uuid) AND path = :p", r=role_id, p=path)

    def allowed_paths(self, tenant_id: str, email: str) -> Set[str]:
        """Every endpoint path the roles this person holds allow."""
        return {r["path"] for r in db.rows("""SELECT DISTINCT p.path FROM role_permissions p JOIN role_mails m ON m.role_id = p.role_id
                                              JOIN roles r ON r.role_id = p.role_id
                                              WHERE r.tenant_id = CAST(:t AS uuid) AND r.active AND m.mail = :m""", t=tenant_id, m=email.strip().lower())}

    # ---- the mails sent to the root ----
    def log_mail(self, tenant_id: str, event_type: str, role_id: Optional[str], actor: Optional[str], message: str) -> None:
        db.run("""INSERT INTO root_mail_log (tenant_id, event_type, role_id, actor, message)
                  VALUES (CAST(:t AS uuid), :e, CAST(:r AS uuid), :a, :m)""", t=tenant_id, e=event_type, r=role_id, a=actor, m=message)

    def mail_log(self, tenant_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        return db.rows("""SELECT to_char(at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI') AS at, event_type, role_id::text AS role_id, actor, message
                          FROM root_mail_log WHERE tenant_id = CAST(:t AS uuid) ORDER BY id DESC LIMIT :n""", t=tenant_id, n=limit)

    # ---- the storefront template, with how each role sees the workspace ----
    def get_template(self, tenant_id: str) -> Dict[str, Any]:
        row = db.one("SELECT data FROM templates WHERE tenant_id = CAST(:t AS uuid)", t=tenant_id)
        if row is None:
            return {}
        return row["data"] if isinstance(row["data"], dict) else json.loads(row["data"])

    def save_template(self, tenant_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        db.run("""INSERT INTO templates (tenant_id, data) VALUES (CAST(:t AS uuid), CAST(:d AS jsonb))
                  ON CONFLICT (tenant_id) DO UPDATE SET data = EXCLUDED.data""", t=tenant_id, d=json.dumps(data))
        return data

roles = RoleStore()
