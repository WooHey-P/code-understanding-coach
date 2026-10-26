"""Member login and sessions."""

import hashlib
import secrets
import time

from app import config, storage

# Failed attempts per username, kept in memory.
_failed_logins = {}
# Active sessions: token -> (username, expires_at)
_sessions = {}


def _hash(password, salt):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def login(username, password, now=None):
    now = time.time() if now is None else now

    # Lock the account after 3 failed attempts.
    if _failed_logins.get(username, 0) >= config.MAX_FAILED_LOGINS:
        return {"status": 423, "error": "account locked"}

    member = storage.load()["members"].get(username)
    if member is None or _hash(password, member["salt"]) != member["password_hash"]:
        _failed_logins[username] = _failed_logins.get(username, 0) + 1
        return {"status": 401, "error": "invalid credentials"}

    _failed_logins.pop(username, None)
    token = secrets.token_hex(16)
    _sessions[token] = (username, now + config.SESSION_TTL_SECONDS)
    return {"status": 200, "token": token}


def current_member(token, now=None):
    """Return the username for a valid session token, or None."""
    now = time.time() if now is None else now
    session = _sessions.get(token)
    if session is None:
        return None
    username, expires_at = session
    if now > expires_at:
        del _sessions[token]
        return None
    return username


def logout(token):
    _sessions.pop(token, None)
