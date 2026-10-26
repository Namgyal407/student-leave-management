"""Leave type routes (read: any user, write: admin)."""
from flask import Blueprint, jsonify
from sqlalchemy.exc import IntegrityError

from auth.jwt_handler import role_required, token_required
from db import get_session
from models import LeaveType
from .utils import error, json_body

bp = Blueprint("leave_types", __name__, url_prefix="/api/leave-types")


def _apply(lt, data, creating):
    """Validate and apply fields; returns an error response or None."""
    if creating or "name" in data:
        name = data.get("name")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 50:
            return error("name is required (max 50 characters)", 400)
        lt.name = name.strip()
    if "description" in data:
        if data["description"] is not None and not isinstance(data["description"], str):
            return error("description must be a string", 400)
        lt.description = data["description"]
    if "max_days" in data:
        md = data["max_days"]
        if not isinstance(md, int) or isinstance(md, bool) or md < 1:
            return error("max_days must be a positive integer", 400)
        lt.max_days = md
    for flag in ("requires_doc", "is_active"):
        if flag in data:
            if not isinstance(data[flag], bool):
                return error(f"{flag} must be a boolean", 400)
            setattr(lt, flag, data[flag])
    return None


@bp.get("")
@token_required
def list_types():
    db = get_session()
    types = db.query(LeaveType).filter(LeaveType.is_active.is_(True)).order_by(LeaveType.id).all()
    return jsonify({"leave_types": [t.to_dict() for t in types]}), 200


@bp.post("")
@role_required("admin")
def create_type():
    db = get_session()
    lt = LeaveType()
    err = _apply(lt, json_body(), creating=True)
    if err:
        return err
    db.add(lt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return error("A leave type with that name already exists", 409)
    return jsonify({"leave_type": lt.to_dict()}), 201


@bp.put("/<int:type_id>")
@role_required("admin")
def update_type(type_id):
    db = get_session()
    lt = db.get(LeaveType, type_id)
    if lt is None:
        return error("Leave type not found", 404)
    err = _apply(lt, json_body(), creating=False)
    if err:
        return err
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return error("A leave type with that name already exists", 409)
    return jsonify({"leave_type": lt.to_dict()}), 200
