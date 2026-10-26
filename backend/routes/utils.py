"""Shared helpers for route modules."""
from datetime import date

from flask import jsonify, request

from db import get_session
from models import AuditLog, Notification, User


def error(message, status=400):
    return jsonify({"error": message}), status


def json_body():
    """Return the JSON body as a dict ({} if missing/invalid)."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def current_user():
    """Load the authenticated user from the JWT. None if gone or deactivated."""
    user = get_session().get(User, request.user["user_id"])
    if user is None or not user.is_active:
        return None
    return user


def parse_date(value):
    """Parse 'YYYY-MM-DD' into a date; None if invalid."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def notify(db, user_id, title, message, type_="info", leave_id=None):
    db.add(Notification(user_id=user_id, title=title[:100], message=message,
                        type=type_, related_leave_id=leave_id))


def audit(db, user_id, action, entity_type=None, entity_id=None, new_value=None):
    db.add(AuditLog(user_id=user_id, action=action, entity_type=entity_type,
                    entity_id=entity_id, new_value=new_value,
                    ip_address=(request.remote_addr or "")[:45]))
