from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

from .extensions import db
from .models import User


def login_required(view):
    """Authenticate a request and make its user available as g.current_user."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": {"code": "MISSING_TOKEN", "message": "Authorization token required"}}), 401

        token = auth_header.split(" ", 1)[1].strip()
        secret = current_app.config.get("JWT_SECRET")
        if not token or not secret:
            return jsonify({"error": {"code": "INVALID_TOKEN", "message": "Invalid or unavailable authentication token"}}), 401

        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            user_id = int(payload["sub"])
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
            return jsonify({"error": {"code": "INVALID_TOKEN", "message": "Invalid token"}}), 401

        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"error": {"code": "USER_NOT_FOUND", "message": "User not found"}}), 401

        g.current_user = user
        return view(*args, **kwargs)

    return wrapped


def require_record_owner(record):
    """Return a 403 response when the authenticated user does not own record."""
    if record.owner_id != g.current_user.id:
        return jsonify({
            "error": {
                "code": "FORBIDDEN",
                "message": "You can only access or change your own records."
            }
        }), 403
    return None
