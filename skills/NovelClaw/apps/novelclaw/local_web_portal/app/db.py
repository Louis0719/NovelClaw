from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from .settings import settings


def _apply_sqlite_pragmas(dbapi_connection) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA busy_timeout=30000;")
        try:
            row = cursor.execute("PRAGMA journal_mode=WAL;").fetchone()
            journal_mode = str(row[0]).lower() if row and row[0] else ""
            if journal_mode != "wal":
                cursor.execute("PRAGMA journal_mode=DELETE;")
        except Exception:
            cursor.execute("PRAGMA journal_mode=DELETE;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
    finally:
        cursor.close()


def _build_engine(database_url: str):
    is_sqlite = database_url.startswith("sqlite")
    connect_args = {"check_same_thread": False, "timeout": 30} if is_sqlite else {}
    built = create_engine(
        database_url,
        future=True,
        connect_args=connect_args,
        poolclass=NullPool if is_sqlite else None,
    )
    if is_sqlite:
        @event.listens_for(built, "connect")
        def _sqlite_pragmas(dbapi_connection, connection_record):  # type: ignore[no-redef]
            _apply_sqlite_pragmas(dbapi_connection)

    return built


engine = _build_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

auth_engine = _build_engine(settings.auth_database_url) if settings.auth_database_url else None
AuthSessionLocal = (
    sessionmaker(bind=auth_engine, autoflush=False, autocommit=False, future=True)
    if auth_engine is not None
    else None
)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def open_auth_db() -> Session | None:
    if AuthSessionLocal is None:
        return None
    return AuthSessionLocal()
