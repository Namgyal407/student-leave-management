"""Authenticated supporting-document upload/download for leave requests.

Files are private, size-limited, and stored on disk. A Docker named volume
persists them across restarts. This module does not require a schema migration.
"""
import os
import re
import uuid
from pathlib import Path
from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from sqlalchemy import false

from auth.jwt_handler import token_required, role_required
from db import get_session
from models import LeaveApplication, User
from .utils import current_user, error

bp = Blueprint("attachments", __name__, url_prefix="/api/attachments")
ALLOWED = {"pdf", "png", "jpg", "jpeg"}
MAX_BYTES = 5 * 1024 * 1024


def _folder():
    folder = Path(os.getenv("UPLOAD_FOLDER", str(Path(__file__).resolve().parents[2] / "uploads")))
    folder.mkdir(parents=True, exist_ok=True)
    return folder


@bp.post("")
@role_required("student")
def upload_document():
    user = current_user()
    if user is None:
        return error("User not found or deactivated", 401)
    file = request.files.get("file")
    if file is None or not file.filename:
        return error("Choose a PDF, PNG, or JPEG file", 400)
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED:
        return error("Only PDF, PNG, and JPEG attachments are accepted", 400)
    data = file.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        return error("File must be between 1 byte and 5 MB", 400)
    # Validate magic bytes so extensions cannot masquerade as file types.
    if ext == "pdf" and not data.startswith(b"%PDF-"):
        return error("The selected file is not a valid PDF", 400)
    if ext in ("jpg", "jpeg") and not data.startswith(b"\xff\xd8\xff"):
        return error("The selected file is not a valid JPEG", 400)
    if ext == "png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return error("The selected file is not a valid PNG", 400)
    filename = f"{user.id}_{uuid.uuid4().hex}.{ext}"
    (_folder() / filename).write_bytes(data)
    return jsonify({"document_url": f"/api/attachments/{filename}",
                    "name": secure_filename(file.filename)}), 201


@bp.get("/<string:filename>")
@token_required
def download_document(filename):
    user = current_user()
    if user is None:
        return error("User not found or deactivated", 401)
    if not re.fullmatch(r"\d+_[0-9a-f]{32}\.(pdf|jpg|jpeg|png)", filename):
        return error("Document not found", 404)
    owner_id = int(filename.split("_", 1)[0])
    # Owner access supports uploads that have not yet been linked to a leave.
    allowed = user.id == owner_id
    if not allowed:
        db = get_session()
        q = (db.query(LeaveApplication).join(User, User.id == LeaveApplication.student_id)
             .filter(LeaveApplication.document_url == f"/api/attachments/{filename}"))
        if user.role == "faculty":
            q = q.filter(User.department == user.department) if user.department else q.filter(false())
        elif user.role != "admin":
            return error("Document not found", 404)
        allowed = q.first() is not None
    if not allowed:
        return error("Document not found", 404)
    response = send_from_directory(_folder(), filename, as_attachment=True)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
