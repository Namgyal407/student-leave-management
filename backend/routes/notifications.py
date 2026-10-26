"""In-app notifications for the logged-in user."""
from flask import Blueprint, jsonify, request

from auth.jwt_handler import token_required
from db import get_session
from models import Notification
from .utils import error

bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@bp.get("")
@token_required
def list_notifications():
    db = get_session()
    uid = request.user["user_id"]
    q = db.query(Notification).filter(Notification.user_id == uid)
    unread_count = q.filter(Notification.is_read.is_(False)).count()
    if request.args.get("unread", "").lower() in ("1", "true", "yes"):
        q = q.filter(Notification.is_read.is_(False))
    limit = min(max(request.args.get("limit", 50, type=int), 1), 200)
    items = q.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit).all()
    return jsonify({"notifications": [n.to_dict() for n in items],
                    "unread_count": unread_count}), 200


@bp.post("/read-all")
@token_required
def read_all():
    db = get_session()
    n = (db.query(Notification)
           .filter(Notification.user_id == request.user["user_id"],
                   Notification.is_read.is_(False))
           .update({"is_read": True}, synchronize_session=False))
    db.commit()
    return jsonify({"updated": n}), 200


@bp.post("/<int:notification_id>/read")
@token_required
def mark_read(notification_id):
    db = get_session()
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != request.user["user_id"]:
        return error("Notification not found", 404)
    n.is_read = True
    db.commit()
    return jsonify({"notification": n.to_dict()}), 200
