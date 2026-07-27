from __future__ import annotations

from functools import lru_cache
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from .models import User
from .settings import settings


@lru_cache(maxsize=1)
def _auth_engine():
    auth_database_url = (settings.auth_database_url or "").strip()
    if not auth_database_url:
        return None
    is_sqlite = auth_database_url.startswith("sqlite")
    connect_args = {"check_same_thread": False, "timeout": 30} if is_sqlite else {}
    return create_engine(
        auth_database_url,
        future=True,
        connect_args=connect_args,
        poolclass=NullPool if is_sqlite else None,
    )


def sync_user_from_auth_db(db: Session, user_id: int) -> Optional[User]:
    local_user = db.get(User, user_id)
    engine = _auth_engine()
    if engine is None:
        return local_user

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, email, password_hash
                FROM users
                WHERE id = :user_id
                """
            ),
            {"user_id": user_id},
        ).mappings().first()

    if row is None:
        return local_user

    email = str(row["email"] or "").strip().lower()
    password_hash = str(row["password_hash"] or "")
    changed = False

    if local_user is None:
        local_user = User(
            id=int(row["id"]),
            email=email,
            password_hash=password_hash,
        )
        db.add(local_user)
        changed = True
    else:
        if email and local_user.email != email:
            local_user.email = email
            changed = True
        if password_hash and local_user.password_hash != password_hash:
            local_user.password_hash = password_hash
            changed = True

    if changed:
        db.commit()
        db.refresh(local_user)

    return local_user
