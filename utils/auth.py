"""
utils/auth.py - Authentication helpers
Provides JWT creation, login_required and admin_required decorators,
and a helper to retrieve the current user from session.
"""
import jwt
from functools import wraps
from datetime import datetime, timedelta, timezone
from flask import request, session, redirect, url_for, flash, jsonify
from config import Config


# ─── Token helpers ────────────────────────────────────────────────────────────

def create_token(user_id: str, email: str, role: str = 'user') -> str:
    """Create a signed JWT for the given user."""
    payload = {
        'user_id': user_id,
        'email':   email,
        'role':    role,
        'exp':     datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')


def decode_token(token: str):
    """Decode and verify a JWT. Returns payload dict or None."""
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ─── Current-user helper ──────────────────────────────────────────────────────

def get_current_user():
    """
    Return the decoded JWT payload from the session token, or None if
    the user is not logged in / token is invalid.
    """
    token = session.get('token')
    if not token:
        return None
    return decode_token(token)


# ─── Decorators ───────────────────────────────────────────────────────────────

def login_required(f):
    """Decorator: require a valid session token.
    Sets request.user to the decoded payload before calling the view.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))

        payload = decode_token(token)
        if not payload:
            session.clear()
            if request.is_json:
                return jsonify({'error': 'Session expired. Please log in again.'}), 401
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))

        request.user = payload
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator: require a valid session token AND admin role.
    Sets request.user to the decoded payload before calling the view.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))

        payload = decode_token(token)
        if not payload:
            session.clear()
            if request.is_json:
                return jsonify({'error': 'Session expired. Please log in again.'}), 401
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))

        if payload.get('role') != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            flash('Access denied. Admins only.', 'danger')
            return redirect(url_for('products.index'))

        request.user = payload
        return f(*args, **kwargs)
    return decorated
