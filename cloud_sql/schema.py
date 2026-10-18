"""
Cloud SQL (PostgreSQL) - schema.
Every statement is safe to run again, so the service can apply the schema each time it starts.
Ids are UUIDs made by the database. Money is never stored here: usage and billing live in BigQuery.
"""

import logging

from sqlalchemy import text

from cloud_sql import db

log = logging.getLogger("lakshmi.schema")

STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS tenants (
        tenant_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name       text NOT NULL UNIQUE,
        type       text NOT NULL DEFAULT '',
        status     text NOT NULL DEFAULT 'Active',
        profile    jsonb NOT NULL DEFAULT '{}'::jsonb,
        created_at timestamptz NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS users (
        user_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name       text NOT NULL,
        email      text NOT NULL,
        role       text NOT NULL,
        tenant_id  uuid REFERENCES tenants(tenant_id) ON DELETE CASCADE,
        created_at timestamptz NOT NULL DEFAULT now()
    )""",
    "CREATE UNIQUE INDEX IF NOT EXISTS users_email_key ON users (lower(email))",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences jsonb NOT NULL DEFAULT '{}'::jsonb",
    """CREATE TABLE IF NOT EXISTS accounts (
        email                text PRIMARY KEY,
        password_hash        text NOT NULL,
        user_id              uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        portal               text NOT NULL,
        active               boolean NOT NULL DEFAULT true,
        must_change_password boolean NOT NULL DEFAULT false,
        failed_attempts      integer NOT NULL DEFAULT 0,
        locked_until         timestamptz,
        last_login           timestamptz,
        created_at           timestamptz NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE IF NOT EXISTS entitlements (
        tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
        path      text NOT NULL,
        PRIMARY KEY (tenant_id, path)
    )""",
    """CREATE TABLE IF NOT EXISTS endpoint_settings (
        tenant_id uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
        path      text NOT NULL,
        settings  jsonb NOT NULL,
        PRIMARY KEY (tenant_id, path)
    )""",
    """CREATE TABLE IF NOT EXISTS audit_log (
        id        bigserial PRIMARY KEY,
        at        timestamptz NOT NULL DEFAULT now(),
        tenant_id uuid,
        path      text NOT NULL,
        method    text NOT NULL,
        status    integer NOT NULL,
        code      text NOT NULL,
        ms        real
    )""",
    "CREATE INDEX IF NOT EXISTS audit_log_tenant_at ON audit_log (tenant_id, at DESC)",
    "ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS demo boolean NOT NULL DEFAULT false",
    """CREATE TABLE IF NOT EXISTS roles (
        role_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id   uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
        name        text NOT NULL,
        description text NOT NULL DEFAULT '',
        active      boolean NOT NULL DEFAULT true,
        created_at  timestamptz NOT NULL DEFAULT now()
    )""",
    "CREATE UNIQUE INDEX IF NOT EXISTS roles_name_key ON roles (tenant_id, lower(name))",
    """CREATE TABLE IF NOT EXISTS role_mails (
        role_id uuid NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
        mail    text NOT NULL,
        status  text NOT NULL DEFAULT 'active',
        PRIMARY KEY (role_id, mail)
    )""",
    """CREATE TABLE IF NOT EXISTS role_permissions (
        role_id uuid NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
        path    text NOT NULL,
        PRIMARY KEY (role_id, path)
    )""",
    """CREATE TABLE IF NOT EXISTS templates (
        tenant_id uuid PRIMARY KEY REFERENCES tenants(tenant_id) ON DELETE CASCADE,
        data      jsonb NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS root_mail_log (
        id         bigserial PRIMARY KEY,
        tenant_id  uuid NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
        at         timestamptz NOT NULL DEFAULT now(),
        event_type text NOT NULL,
        role_id    uuid,
        actor      text,
        message    text NOT NULL
    )""",
    # the demo's in-app mailbox: every mail the app "sends" is kept here, with the link in it, instead of leaving the system
    """CREATE TABLE IF NOT EXISTS mailbox (
        id       bigserial PRIMARY KEY,
        to_email text NOT NULL,
        at       timestamptz NOT NULL DEFAULT now(),
        kind     text NOT NULL,
        subject  text NOT NULL,
        body     text NOT NULL,
        link     text
    )""",
    "CREATE INDEX IF NOT EXISTS mailbox_to ON mailbox (lower(to_email), id DESC)",
]

def ensure_schema() -> None:
    with db.tx() as conn:
        for statement in STATEMENTS:
            conn.execute(text(statement))
    log.info("schema ready")
