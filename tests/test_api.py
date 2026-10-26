"""API tests. Need the seeded PostgreSQL database (python database/seed.py).
Re-run the seed to reset data after a test run."""
import uuid
from datetime import date, timedelta


def test_health(client):
    assert client.get("/api/health").status_code == 200


def test_login_ok(client):
    r = client.post("/api/login", json={"email": "student@cst.edu.bt", "password": "password123"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["token"] and body["user"]["role"] == "student"
    assert "password_hash" not in body["user"]


def test_login_email_case_insensitive(client):
    r = client.post("/api/login", json={"email": " Student@CST.edu.bt ", "password": "password123"})
    assert r.status_code == 200


def test_login_bad_password(client):
    r = client.post("/api/login", json={"email": "student@cst.edu.bt", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    assert client.post("/api/login", json={"email": "no@one.bt", "password": "x"}).status_code == 401


def test_login_missing_fields(client):
    assert client.post("/api/login", json={"email": "student@cst.edu.bt"}).status_code == 400
    assert client.post("/api/login", data="not json").status_code == 400


def test_auth_required(client):
    assert client.get("/api/leaves").status_code == 401
    assert client.get("/api/leaves", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_me(client, student):
    assert client.get("/api/me", headers=student).get_json()["user"]["email"] == "student3@cst.edu.bt"


def test_leave_types(client, student):
    r = client.get("/api/leave-types", headers=student)
    assert {t["name"] for t in r.get_json()["leave_types"]} >= {"Medical", "Personal"}


def test_student_sees_only_own_leaves(client, student):
    leaves = client.get("/api/leaves", headers=student).get_json()["leaves"]
    assert leaves and all(l["student_email"] == "student3@cst.edu.bt" for l in leaves)


def test_full_leave_lifecycle(client, student, faculty_it, faculty_cs):
    start = date.today() + timedelta(days=200 + uuid.uuid4().int % 100)
    payload = {"leave_type_id": 2, "reason": "Test personal leave",
               "start_date": str(start), "end_date": str(start + timedelta(days=1))}

    r = client.post("/api/leaves", json=payload, headers=student)
    assert r.status_code == 201, r.get_json()
    leave = r.get_json()["leave"]
    assert leave["status"] == "pending" and leave["total_days"] == 2

    # overlapping request is rejected
    assert client.post("/api/leaves", json=payload, headers=student).status_code == 409

    # faculty from another department cannot see or review it
    assert client.get(f"/api/leaves/{leave['id']}", headers=faculty_cs).status_code == 404
    # rejecting needs a comment
    url = f"/api/leaves/{leave['id']}/review"
    assert client.post(url, json={"action": "reject"}, headers=faculty_it).status_code == 400
    # students cannot review
    assert client.post(url, json={"action": "approve"}, headers=student).status_code == 403

    r = client.post(url, json={"action": "approve", "comment": "Enjoy"}, headers=faculty_it)
    assert r.status_code == 200
    reviewed = r.get_json()["leave"]
    assert reviewed["status"] == "approved" and reviewed["reviewed_at"]
    assert reviewed["reviewer_name"] == "Mr. Ugyen Tshering"

    # already reviewed
    assert client.post(url, json={"action": "approve"}, headers=faculty_it).status_code == 409

    # student was notified
    notes = client.get("/api/notifications?unread=true", headers=student).get_json()
    assert notes["unread_count"] >= 1
    assert any(n["related_leave_id"] == leave["id"] for n in notes["notifications"])

    # future approved leave can be cancelled
    r = client.post(f"/api/leaves/{leave['id']}/cancel", headers=student)
    assert r.status_code == 200 and r.get_json()["leave"]["status"] == "cancelled"


def test_validation(client, student):
    bad = {"leave_type_id": 2, "reason": "x", "start_date": "2027-01-10", "end_date": "2027-01-01"}
    assert client.post("/api/leaves", json=bad, headers=student).status_code == 400
    too_long = {"leave_type_id": 2, "reason": "x", "start_date": "2027-03-01", "end_date": "2027-04-30"}
    assert client.post("/api/leaves", json=too_long, headers=student).status_code == 400
    no_doc = {"leave_type_id": 1, "reason": "x", "start_date": "2027-05-01", "end_date": "2027-05-02"}
    assert client.post("/api/leaves", json=no_doc, headers=student).status_code == 400


def test_admin_only(client, student, admin):
    assert client.get("/api/users", headers=student).status_code == 403
    assert client.get("/api/users", headers=admin).status_code == 200


def test_admin_creates_user(client, admin):
    email = f"new{uuid.uuid4().hex[:8]}@cst.edu.bt"
    body = {"name": "New Student", "email": email, "password": "password123",
            "role": "student", "year": "2nd Year", "department": "Computer Science"}
    assert client.post("/api/users", json=body, headers=admin).status_code == 201
    assert client.post("/api/users", json=body, headers=admin).status_code == 409
    r = client.post("/api/login", json={"email": email, "password": "password123"})
    assert r.status_code == 200
