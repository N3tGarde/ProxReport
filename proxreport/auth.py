from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class UserRecord:
    salt_hex: str
    sha256_hex: str


_USERS_LOCK = threading.Lock()
_USERS_CACHE: Dict[str, UserRecord] = {}
_USERS_MTIME: Optional[float] = None


def _sha256_hex(salt_bytes: bytes, password_utf8: str) -> str:
    h = hashlib.sha256()
    h.update(salt_bytes)
    h.update(password_utf8.encode("utf-8"))
    return h.hexdigest()


def _load_users(users_file: str) -> Dict[str, UserRecord]:
    users: Dict[str, UserRecord] = {}

    p = Path(users_file)
    data = p.read_text(encoding="utf-8")
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # username:salt_hex:sha256_hex
        parts = line.split(":")
        if len(parts) != 3:
            continue
        username, salt_hex, sha256_hex = parts
        username = username.strip()
        salt_hex = salt_hex.strip()
        sha256_hex = sha256_hex.strip()
        if not username or not salt_hex or not sha256_hex:
            continue
        users[username] = UserRecord(salt_hex=salt_hex, sha256_hex=sha256_hex)

    return users


def get_users(users_file: str) -> Dict[str, UserRecord]:
    global _USERS_CACHE, _USERS_MTIME

    p = Path(users_file)
    mtime = p.stat().st_mtime

    with _USERS_LOCK:
        if _USERS_MTIME is None or mtime != _USERS_MTIME:
            _USERS_CACHE = _load_users(users_file)
            _USERS_MTIME = mtime
        return dict(_USERS_CACHE)


def parse_basic_auth(header_value: str) -> Optional[Tuple[str, str]]:
    # header_value: "Basic <base64(user:pass)>"
    try:
        scheme, b64 = header_value.split(" ", 1)
        if scheme.lower() != "basic":
            return None
        raw = base64.b64decode(b64.strip()).decode("utf-8")
        if ":" not in raw:
            return None
        username, password = raw.split(":", 1)
        return username, password
    except Exception:
        return None


def check_password(users_file: str, username: str, password: str) -> bool:
    try:
        users = get_users(users_file)
        rec = users.get(username)
        if rec is None:
            return False
        salt_bytes = bytes.fromhex(rec.salt_hex)
        candidate = _sha256_hex(salt_bytes, password)
        return hmac.compare_digest(candidate, rec.sha256_hex)
    except Exception:
        return False


def require_basic_auth(handler, users_file: str, realm: str = "proxreport") -> bool:
    header = handler.headers.get("Authorization")
    if not header:
        _send_unauthorized(handler, realm)
        return False

    parsed = parse_basic_auth(header)
    if parsed is None:
        _send_unauthorized(handler, realm)
        return False

    username, password = parsed
    if not check_password(users_file, username, password):
        _send_unauthorized(handler, realm)
        return False

    return True


def _send_unauthorized(handler, realm: str) -> None:
    handler.send_response(401)
    handler.send_header("WWW-Authenticate", f'Basic realm="{realm}", charset="UTF-8"')
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.end_headers()
    handler.wfile.write(b"Unauthorized\n")
