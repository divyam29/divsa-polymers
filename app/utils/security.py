"""Startup validation and shared, atomic admin login throttling."""
from datetime import datetime, timezone
import hashlib
import hmac
import time

from flask import current_app, request
from pymongo import ReturnDocument, timeout
from pymongo.errors import PyMongoError
from werkzeug.security import check_password_hash

from app.db import get_db


def validate_security_config(app):
    secret = app.config.get('SECRET_KEY')
    if not isinstance(secret, str) or len(secret) < 32:
        raise RuntimeError('Set SECRET_KEY to a random secret of at least 32 characters.')
    password_hash = app.config.get('ADMIN_PASSWORD_HASH') or ''
    try:
        method, salt, digest = password_hash.split('$')
        if not method.startswith(('scrypt:', 'pbkdf2:')) or not salt or len(digest) < 64:
            raise ValueError
        int(digest, 16)
        check_password_hash(password_hash, 'configuration-validation-only')
    except (ValueError, TypeError):
        raise RuntimeError('Set ADMIN_PASSWORD_HASH using scripts/generate_hash.py.') from None


class LoginLimitUnavailable(Exception):
    pass


def check_login_limit():
    """Allow five attempts per client per 15-minute fixed window across workers.

    Use the server's remote address, never an untrusted forwarded header.
    MongoDB is shared by serverless instances; failures deny login rather than
    silently falling back to an ineffective per-process limit.
    """
    window = current_app.config['ADMIN_LOGIN_WINDOW_SECONDS']
    now = int(time.time())
    bucket = now // window
    reset_at = (bucket + 1) * window
    identity = hmac.new(
        current_app.secret_key.encode(),
        (request.remote_addr or 'unknown').encode(), hashlib.sha256,
    ).hexdigest()
    try:
        with timeout(3):
            db = get_db()
            if db is None:
                raise LoginLimitUnavailable
            counters = db.admin_login_attempts
            counters.create_index('expires_at', expireAfterSeconds=0)
            result = counters.find_one_and_update(
                {'_id': f'{identity}:{bucket}'},
                {'$inc': {'count': 1}, '$setOnInsert': {
                    'expires_at': datetime.fromtimestamp(reset_at, timezone.utc),
                }},
                upsert=True, return_document=ReturnDocument.AFTER,
            )
    except PyMongoError:
        current_app.logger.error('Admin login rate-limit storage is unavailable.')
        raise LoginLimitUnavailable from None
    return reset_at - now if result['count'] > current_app.config['ADMIN_LOGIN_LIMIT'] else 0
