from __future__ import annotations

import os
import secrets
from pathlib import Path

from .settings import DATA_DIR, settings


SESSION_SECRET_FILE = DATA_DIR / "session.secret"


def _write_secret_file(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _get_or_create_session_secret() -> str:
    if settings.session_secret_env:
        return settings.session_secret_env
    if SESSION_SECRET_FILE.exists():
        return SESSION_SECRET_FILE.read_text(encoding="utf-8").strip()

    value = secrets.token_urlsafe(64)
    _write_secret_file(SESSION_SECRET_FILE, value)
    return value


SESSION_SECRET = _get_or_create_session_secret()
