"""User management (admin only), plus a faculty/admin student directory."""
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from auth.jwt_handler import role_required
from auth.password import hash_password
from db import get_session
from models import User
from .utils import audit, current_user, error, json_body

bp = Blueprint("users", __name__, url_prefix="/api/users")

ROLES = ("student", "faculty", "admin")
YEARS = ("1st Year", "2nd Year", "3rd Year", "4th Year", "Final Year")


def _str_or_none(data, key, max_len):
    v = data.get(key)
    if v is None:
        return None, None
    if not isinstance(v, str) or len(v) > max_len:
        return None, error(f"{key} must be a string of at most {max_len} characters", 400)
    return (v.strip() or None), None


@bp.get("")
@role_required("admin")
def list_users():
    db = get_session()
    q = db.query(User)
    role = request.args.get("role")
    if role:
        if role not in ROLES:
            return error(f"role must be one of {', '.join(ROLES)}", 400)
        q = q.filter(User.role == role)
    users = q.order_by(User.id).all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200


@bp.post("")
@role_required("admin")
def create_user():
    db = get_session()
    data = json_body()

    name, email, password = data.get("name"), data.get("email"), data.get("password")
    if not all(isinstance(v, str) and v.strip() for v in (name, email, password)):
        return error("name, email and password are required", 400)
    if len(name.strip()) > 100 or len(email.strip()) > 100 or "@" not in email:
        return error("Invalid name or email", 400)
    if len(password) < 8:
        return error("Password must be at least 8 characters", 400)
    role = data.get("role")
    if role not in ROLES:
        return error(f"role must be one of {', '.join(ROLES)}", 400)

    year = data.get("year")
    if role == "student":
        if year not in YEARS:
            return error(f"year is required for students: {', '.join(YEARS)}", 400)
    elif year is not None:
        return error("year is only allowed for students", 400)

    department, err = _str_or_none(data, "department", 100)
    if err:
        return err
    phone, err = _str_or_none(data, "phone", 20)
    if err:
        return err

    if db.query(User.id).filter(func.lower(User.email) == email.strip().lower()).first():
        return error("A user with that email already exists", 409)

    user = User(name=name.strip(), email=email.strip().lower(),
                password_hash=hash_password(password), role=role, year=year,
                department=department, phone=phone)
    db.add(user)
    try:
        db.flush()
        audit(db, current_user().id, "USER_CREATE", "user", user.id,
              {"email": user.email, "role": role})
        db.commit()
    except IntegrityError:
        db.rollback()
        return error("Could not create user (duplicate or invalid data)", 409)
    return jsonify({"user": user.to_dict()}), 201


@bp.put("/<int:user_id>")
@role_required("admin")
def update_user(user_id):
    db = get_session()
    user = db.get(User, user_id)
    if user is None:
        return error("User not found", 404)
    data = json_body()

    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip() or len(data["name"]) > 100:
            return error("Invalid name", 400)
        user.name = data["name"].strip()
    for key, limit in (("department", 100), ("phone", 20)):
        if key in data:
            value, err = _str_or_none(data, key, limit)
            if err:
                return err
            setattr(user, key, value)
    if "year" in data:
        if user.role == "student":
            if data["year"] not in YEARS:
                return error(f"year must be one of {', '.join(YEARS)}", 400)
            user.year = data["year"]
        elif data["year"] is not None:
            return error("year is only allowed for students", 400)
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return error("is_active must be a boolean", 400)
        if user.id == request.user["user_id"] and not data["is_active"]:
            return error("You cannot deactivate your own account", 400)
        user.is_active = data["is_active"]
    if "password" in data:
        if not isinstance(data["password"], str) or len(data["password"]) < 8:
            return error("Password must be at least 8 characters", 400)
        user.password_hash = hash_password(data["password"])

    audit(db, request.user["user_id"], "USER_UPDATE", "user", user.id)
    db.commit()
    return jsonify({"user": user.to_dict()}), 200
