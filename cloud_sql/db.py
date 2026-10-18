"""
Cloud SQL (PostgreSQL) - connection.
One pooled engine for the whole process, built on first use. It connects through the Cloud SQL connector, so it
needs no open port and no key file: on Cloud Run it signs in as the service account, and on a laptop it uses
`gcloud auth application-default login`.

Settings come from environment variables:
    DB_PASSWORD   the password of the application user (required; on Cloud Run it comes from Secret Manager)
    DB_USER       default lakshmi_app
    DB_NAME       default lakshmi
    DB_INSTANCE   default ennovators:us-central1:lakshmi-db
"""

import logging
import os
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

log = logging.getLogger("lakshmi.db")

_engine: Optional[Engine] = None
_lock = threading.Lock()

def configured() -> bool:
    return bool(os.environ.get("DB_PASSWORD"))

def _build() -> Engine:
    from google.cloud.sql.connector import Connector
    instance = os.environ.get("DB_INSTANCE", "ennovators:us-central1:lakshmi-db")
    user = os.environ.get("DB_USER", "lakshmi_app")
    name = os.environ.get("DB_NAME", "lakshmi")
    password = os.environ["DB_PASSWORD"]
    connector = Connector()

    def connect():
        return connector.connect(instance, "pg8000", user=user, password=password, db=name)

    # db-f1-micro allows few connections, so keep the pool small
    return create_engine("postgresql+pg8000://", creator=connect, pool_size=3, max_overflow=2,
                         pool_pre_ping=True, pool_recycle=1800)

def engine() -> Engine:
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                if not configured():
                    raise RuntimeError("DB_PASSWORD is not set: the database is not configured")
                _engine = _build()
    return _engine

@contextmanager
def tx() -> Iterator[Connection]:
    """One transaction: it commits when the block ends and rolls back on an error."""
    with engine().begin() as conn:
        yield conn

def rows(sql: str, **params: Any) -> List[Dict[str, Any]]:
    with engine().connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql), params)]

def one(sql: str, **params: Any) -> Optional[Dict[str, Any]]:
    found = rows(sql, **params)
    return found[0] if found else None

def run(sql: str, **params: Any) -> None:
    with tx() as conn:
        conn.execute(text(sql), params)
