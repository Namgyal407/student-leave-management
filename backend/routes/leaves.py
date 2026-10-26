"""Leave application routes.

Students  : create / list own / edit pending / cancel
Faculty   : list + review leaves of students in their own department
Admin     : everything
"""
from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.orm import aliased

from auth.jwt_handler import role_required, token_required
from db import get_session
from models import LeaveApplication, LeaveType, User
from .utils import audit, current_user, error, json_body, notify, parse_date

bp = Blueprint("leaves", __name__, url_prefix="/api/leaves")

Student = aliased(User)
Reviewer = aliased(User)
VALID_STATUSES = ("pending", "approved", "rejected", "cancelled")


# ---------------------------------------------------------------- helpers
def _base_query(db):
    return (
        db.query(LeaveApplication, Student, LeaveType, Reviewer)
        .join(Student, Student.id == LeaveApplication.student_id)
        .join(LeaveType, LeaveType.id == LeaveApplication.leave_type_id)
        .outerjoin(Reviewer, Reviewer.id == LeaveApplication.reviewed_by)
    )


def _scope(query, user):
    """Restrict a leave query to what `user` is allowed to see."""
    if user.role == "student":
        return query.filter(LeaveApplication.student_id == user.id)
    if user.role == "faculty" and user.department:
        return query.filter(Student.department == user.department)
    return query  # admin (or faculty with no department set)


def _serialize(row):
    leave, student, ltype, reviewer = row
    d = leave.to_dict()
    d.update({
        "total_days": (leave.end_date - leave.start_date).days + 1,
        "leave_type": ltype.name,
        "student_name": student.name,
        "student_email": student.email,
        "student_year": student.year,
        "student_department": student.department,
        "reviewer_name": reviewer.name if reviewer else None,
    })
    return d


def _get_visible(db, user, leave_id):
    return _scope(_base_query(db), user).filter(LeaveApplication.id == leave_id).first()


def _has_overlap(db, student_id, start, end, exclude_id=None):
    q = db.query(LeaveApplication.id).filter(
        LeaveApplication.student_id == student_id,
        LeaveApplication.status.in_(("pending", "approved")),
        LeaveApplication.start_date <= end,
        LeaveApplication.end_date >= start,
    )
    if exclude_id is not None:
        q = q.filter(LeaveApplication.id != exclude_id)
    return db.query(q.exists()).scalar()


def _validate_leave_fields(db, data, student_id, existing=None):
    """Validate create/update payload. Returns (clean_dict, error_response)."""
    clean = {}

    type_id = data.get("leave_type_id", existing.leave_type_id if existing else None)
    if not isinstance(type_id, int) or isinstance(type_id, bool):
        return None, error("leave_type_id (integer) is required", 400)
    ltype = db.get(LeaveType, type_id)
    if ltype is None or not ltype.is_active:
        return None, error("Unknown or inactive leave type", 400)
    clean["leave_type_id"] = type_id

    reason = data.get("reason", existing.reason if existing else None)
    if not isinstance(reason, str) or not reason.strip():
        return None, error("reason is required", 400)
    clean["reason"] = reason.strip()

    start = parse_date(data["start_date"]) if "start_date" in data else (existing.start_date if existing else None)
    end = parse_date(data["end_date"]) if "end_date" in data else (existing.end_date if existing else None)
    if start is None or end is None:
        return None, error("start_date and end_date are required (YYYY-MM-DD)", 400)
    if end < start:
        return None, error("end_date cannot be before start_date", 400)
    days = (end - start).days + 1
    if ltype.max_days and days > ltype.max_days:
        return None, error(f"{ltype.name} leave allows at most {ltype.max_days} days "
                           f"(requested {days})", 400)
    clean["start_date"], clean["end_date"] = start, end

    doc = data.get("document_url", existing.document_url if existing else None)
    if doc is not None and not isinstance(doc, str):
        return None, error("document_url must be a string", 400)
    doc = doc.strip() if isinstance(doc, str) and doc.strip() else None
    if len(doc or "") > 255:
        return None, error("document_url is too long (max 255)", 400)
    if ltype.requires_doc and not doc:
        return None, error(f"{ltype.name} leave requires a supporting document "
                           f"(document_url)", 400)
    clean["document_url"] = doc

    if _has_overlap(db, student_id, start, end, existing.id if existing else None):
        return None, error("You already have a pending or approved leave "
                           "overlapping these dates", 409)
    return clean, None


# ----------------------------------------------------------------- routes
@bp.post("")
@role_required("student")
def create_leave():
    db = get_session()
    user = current_user()
    if user is None:
        return error("User not found or deactivated", 401)

    clean, err = _validate_leave_fields(db, json_body(), user.id)
    if err:
        return err

    leave = LeaveApplication(student_id=user.id, status="pending", **clean)
    db.add(leave)
    db.flush()  # get leave.id

    # Notify faculty of the student's department (fall back to all faculty).
    faculty_q = db.query(User).filter(User.role == "faculty", User.is_active.is_(True))
    faculty = faculty_q.filter(User.department == user.department).all() if user.department else []
    for f in faculty or faculty_q.all():
        notify(db, f.id, "New leave request",
               f"{user.name} requested leave from {clean['start_date']} to {clean['end_date']}.",
               "info", leave.id)
    notify(db, user.id, "Leave submitted",
           "Your leave request was submitted and is awaiting review.", "info", leave.id)
    audit(db, user.id, "LEAVE_CREATE", "leave_application", leave.id,
          {"start_date": str(clean["start_date"]), "end_date": str(clean["end_date"])})
    db.commit()

    return jsonify({"leave": _serialize(_get_visible(db, user, leave.id))}), 201


@bp.get("")
@token_required
def list_leaves():
    db = get_session()
    user = current_user()
    if user is None:
        return error("User not found or deactivated", 401)

    q = _scope(_base_query(db), user)

    status = request.args.get("status")
    if status:
        if status not in VALID_STATUSES:
            return error(f"status must be one of {', '.join(VALID_STATUSES)}", 400)
        q = q.filter(LeaveApplication.status == status)

    student_id = request.args.get("student_id", type=int)
    if student_id is not None and user.role != "student":
        q = q.filter(LeaveApplication.student_id == student_id)

    leave_type_id = request.args.get("leave_type_id", type=int)
    if leave_type_id is not None:
        q = q.filter(LeaveApplication.leave_type_id == leave_type_id)

    limit = min(max(request.args.get("limit", 100, type=int), 1), 500)
    offset = max(request.args.get("offset", 0, type=int), 0)

    total = q.with_entities(func.count(LeaveApplication.id)).scalar()
    rows = (q.order_by(LeaveApplication.submitted_at.desc(), LeaveApplication.id.desc())
              .limit(limit).offset(offset).all())
    return jsonify({"leaves": [_serialize(r) for r in rows],
                    "total": total, "limit": limit, "offset": offset}), 200


@bp.get("/summary")
@token_required
def summary():
    """Counts of visible leaves per status."""
    db = get_session()
    user = current_user()
    if user is None:
        return error("User not found or deactivated", 401)
    q = _scope(_base_query(db), user).with_entities(
        LeaveApplication.status, func.count(LeaveApplication.id)
    ).group_by(LeaveApplication.status)
    counts = {s: 0 for s in VALID_STATUSES}
    counts.update({status: n for status, n in q.all()})
    counts["total"] = sum(counts[s] for s in VALID_STATUSES)
    return jsonify({"summary": counts}), 200


@bp.get("/<int:leave_id>")
@token_required
def get_leave(leave_id):
    db = get_session()
    user = current_user()
    if user is None:
        return error("User not found or deactivated", 401)
    row = _get_visible(db, user, leave_id)
    if row is None:
        return error("Leave not found", 404)
    return jsonify({"leave": _serialize(row)}), 200


@bp.put("/<int:leave_id>")
@role_required("student")
def update_leave(leave_id):
    """Student edits their own leave while it is still pending."""
    db = get_session()
    user = current_user()
    if user is None:
        return error("User not found or deactivated", 401)
    row = _get_visible(db, user, leave_id)
    if row is None:
        return error("Leave not found", 404)
    leave = row[0]
    if leave.status != "pending":
        return error("Only pending leaves can be edited", 409)

    clean, err = _validate_leave_fields(db, json_body(), user.id, existing=leave)
    if err:
        return err
    for k, v in clean.items():
        setattr(leave, k, v)
    db.commit()
    return jsonify({"leave": _serialize(_get_visible(db, user, leave_id))}), 200


@bp.post("/<int:leave_id>/cancel")
@role_required("student")
def cancel_leave(leave_id):
    """Student cancels own leave: pending, or approved and not yet started."""
    db = get_session()
    user = current_user()
    if user is None:
        return error("User not found or deactivated", 401)
    row = _get_visible(db, user, leave_id)
    if row is None:
        return error("Leave not found", 404)
    leave = row[0]

    cancellable = leave.status == "pending" or (
        leave.status == "approved" and leave.start_date > date.today())
    if not cancellable:
        return error(f"A {leave.status} leave cannot be cancelled", 409)

    leave.status = "cancelled"
    notify(db, user.id, "Leave cancelled",
           f"Your leave ({leave.start_date} to {leave.end_date}) was cancelled.",
           "warning", leave.id)
    audit(db, user.id, "LEAVE_CANCEL", "leave_application", leave.id)
    db.commit()
    return jsonify({"leave": _serialize(_get_visible(db, user, leave_id))}), 200


@bp.post("/<int:leave_id>/review")
@role_required("faculty", "admin")
def review_leave(leave_id):
    """Approve or reject a pending leave. Body: {action: approve|reject, comment}."""
    db = get_session()
    user = current_user()
    if user is None:
        return error("User not found or deactivated", 401)

    data = json_body()
    action = data.get("action")
    if action not in ("approve", "reject"):
        return error("action must be 'approve' or 'reject'", 400)
    comment = data.get("comment")
    if comment is not None and not isinstance(comment, str):
        return error("comment must be a string", 400)
    comment = comment.strip() if comment and comment.strip() else None
    if action == "reject" and not comment:
        return error("A comment is required when rejecting a leave", 400)

    row = _get_visible(db, user, leave_id)  # faculty: own department only
    if row is None:
        return error("Leave not found", 404)
    leave = row[0]
    if leave.status != "pending":
        return error(f"Leave is already {leave.status}", 409)

    approved = action == "approve"
    leave.status = "approved" if approved else "rejected"
    leave.reviewed_by = user.id          # DB trigger stamps reviewed_at + audit_log
    leave.reviewer_comment = comment
    notify(db, leave.student_id,
           "Leave approved" if approved else "Leave rejected",
           f"Your leave ({leave.start_date} to {leave.end_date}) was "
           f"{'approved' if approved else 'rejected'} by {user.name}."
           + (f" Comment: {comment}" if comment else ""),
           "success" if approved else "error", leave.id)
    db.commit()
    return jsonify({"leave": _serialize(_get_visible(db, user, leave_id))}), 200
