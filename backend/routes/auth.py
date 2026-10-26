"""Authentication routes: POST /api/login, GET /api/me, POST /api/me/password."""
from flask import Blueprint, jsonify
from sqlalchemy import func

from auth.jwt_handler import generate_token, token_required
from auth.password import hash_password, verify_password
from db import get_session
from models import User
from .utils import audit, current_user, error, json_body

bp = Blueprint("auth", __name__, url_prefix="/api")


@bp.post("/login")
def login():
    data = json_body()
    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not email.strip() \
            or not isinstance(password, str) or not password:
        return error("email and password are required", 400)

    db = get_session()
    user = db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()

    # Same message for unknown email and wrong password (no user enumeration).
    if user is None or not verify_password(password, user.password_hash):
        return error("Invalid email or password", 401)
    if not user.is_active:
        return error("Account is deactivated", 403)

    token = generate_token(user.id, user.role)
    audit(db, user.id, "LOGIN", "user", user.id)
    db.commit()
    return jsonify({"token": token, "user": user.to_dict()}), 200


@bp.get("/me")
@token_required
def me():
    user = current_user()
    if user is None:
        return error("User not found or deactivated", 401)
    return jsonify({"user": user.to_dict()}), 200


@bp.post("/me/password")
@token_required
def change_password():
    user = current_user()
    if user is None:
        return error("User not found or deactivated", 401)
    data = json_body()
    current, new = data.get("current_password"), data.get("new_password")
    if not isinstance(current, str) or not isinstance(new, str):
        return error("current_password and new_password are required", 400)
    if not verify_password(current, user.password_hash):
        return error("Current password is incorrect", 401)
    if len(new) < 8:
        return error("New password must be at least 8 characters", 400)
    db = get_session()
    user.password_hash = hash_password(new)
    audit(db, user.id, "PASSWORD_CHANGE", "user", user.id)
    db.commit()
    return jsonify({"message": "Password updated"}), 200
