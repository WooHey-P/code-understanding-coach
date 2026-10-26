"""Staff login and catalog management. Separate from member login."""

import hashlib
import secrets

from app import catalog, config

_admin_tokens = set()


def admin_login(password):
    if not config.ADMIN_PASSWORD_SHA256:
        return {"status": 503, "error": "admin login not configured"}
    if hashlib.sha256(password.encode("utf-8")).hexdigest() != config.ADMIN_PASSWORD_SHA256:
        return {"status": 401, "error": "invalid credentials"}
    token = secrets.token_hex(16)
    _admin_tokens.add(token)
    return {"status": 200, "token": token}


def is_admin(token):
    return token in _admin_tokens


def add_copies(token, book_id, count):
    if not is_admin(token):
        return {"status": 403, "error": "admins only"}
    return catalog.add_copies(book_id, count)
