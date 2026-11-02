from datetime import datetime, timedelta, timezone

import jwt
from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import User

main_bp = Blueprint("main", __name__)


@main_bp.route("/me", methods=["GET"])
def get_profile():
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return jsonify({"error": {
            "code": "MISSING_TOKEN",
            "message": "Authorization token required"
        }}), 401

    token = auth_header.split(" ", 1)[1]

    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"error": {
            "code": "TOKEN_EXPIRED",
            "message": "Token expired"
        }}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": {
            "code": "INVALID_TOKEN",
            "message": "Invalid token"
        }}), 401

    user = db.session.get(User, int(payload["sub"]))

    if user is None:
        return jsonify({"error": {
            "code": "USER_NOT_FOUND",
            "message": "User not found"
        }}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    }), 200


@main_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "code": "INVALID_JSON",
            "message": "A valid JSON object is required."
        }), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not isinstance(username, str) or not username.strip():
        return jsonify({
            "code": "USERNAME_REQUIRED",
            "message": "Username is required."
        }), 400

    username = username.strip()

    if not 3 <= len(username) <= 30:
        return jsonify({
            "code": "USERNAME_LENGTH_INVALID",
            "message": "Username must be between 3 and 30 characters."
        }), 400

    if not isinstance(email, str) or not email.strip():
        return jsonify({
            "code": "EMAIL_REQUIRED",
            "message": "Email is required."
        }), 400

    email = email.strip().lower()

    if len(email) > 120:
        return jsonify({
            "code": "EMAIL_TOO_LONG",
            "message": "Email must be 120 characters or fewer."
        }), 400

    if not isinstance(password, str) or not password:
        return jsonify({
            "code": "PASSWORD_REQUIRED",
            "message": "Password is required."
        }), 400

    if not 8 <= len(password) <= 128:
        return jsonify({
            "code": "PASSWORD_LENGTH_INVALID",
            "message": "Password must be between 8 and 128 characters."
        }), 400

    if User.query.filter_by(username=username).first():
        return jsonify({
            "code": "USERNAME_CONFLICT",
            "message": "That username is already taken."
        }), 409

    if User.query.filter_by(email=email).first():
        return jsonify({
            "code": "EMAIL_CONFLICT",
            "message": "That email is already registered."
        }), 409

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "code": "REGISTRATION_CONFLICT",
            "message": "That username or email is already registered."
        }), 409

    return jsonify({
        "message": "User registered successfully.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 201

@main_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "code": "INVALID_JSON",
            "message": "A valid JSON object is required."
        }), 400

    identifier = data.get("username") or data.get("email")
    password = data.get("password")

    if not isinstance(identifier, str) or not identifier.strip():
        return jsonify({
            "code": "IDENTIFIER_REQUIRED",
            "message": "Username or email is required."
        }), 400

    if not isinstance(password, str) or not password:
        return jsonify({
            "code": "PASSWORD_REQUIRED",
            "message": "Password is required."
        }), 400

    identifier = identifier.strip()

    user = User.query.filter(
        db.or_(
            User.username == identifier,
            User.email == identifier.lower()
        )
    ).first()

    if user is None or not check_password_hash(
        user.password_hash, password
    ):
        return jsonify({
            "code": "INVALID_CREDENTIALS",
            "message": "Invalid username/email or password."
        }), 401

    jwt_secret = current_app.config.get("JWT_SECRET")
    token_lifetime = current_app.config["JWT_LIFETIME_SECONDS"]

    if not jwt_secret:
        current_app.logger.error("JWT_SECRET is not configured.")
        return jsonify({
            "code": "AUTH_CONFIGURATION_ERROR",
            "message": "Authentication is temporarily unavailable."
        }), 500

    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(
            seconds=token_lifetime
        )
    }

    token = jwt.encode(payload, jwt_secret, algorithm="HS256")

    return jsonify({
        "message": "Login successful.",
        "token": token,
        "token_type": "Bearer",
        "expires_in": token_lifetime
    }), 200
