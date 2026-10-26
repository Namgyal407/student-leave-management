"""
Tests for authentication endpoints.
Run with: pytest tests/test_auth.py -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ============================================================
# SUCCESS CASES (200 OK)
# ============================================================

def test_login_success_student(client):
    """Valid student credentials return 200 + token + role."""
    res = client.post("/api/login", json={
        "email": "student@cst.edu.bt",
        "password": "password123"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "token" in data
    assert data["role"] == "student"
    assert data["name"] == "Sonam Dorji"
    assert data["year"] == "3rd Year"


def test_login_success_faculty(client):
    """Valid faculty credentials return 200 + role=faculty."""
    res = client.post("/api/login", json={
        "email": "faculty@cst.edu.bt",
        "password": "password123"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["role"] == "faculty"
    assert data["year"] is None


def test_login_success_admin(client):
    """Valid admin credentials return 200 + role=admin."""
    res = client.post("/api/login", json={
        "email": "admin@cst.edu.bt",
        "password": "password123"
    })
    assert res.status_code == 200
    assert res.get_json()["role"] == "admin"


def test_login_email_case_insensitive(client):
    """Email is lowercased before lookup (student@ vs STUDENT@)."""
    res = client.post("/api/login", json={
        "email": "STUDENT@CST.EDU.BT",
        "password": "password123"
    })
    assert res.status_code == 200


# ============================================================
# FAILURE CASES (400 & 401)
# ============================================================

def test_login_wrong_password(client):
    """Wrong password returns 401 with exact contract error message."""
    res = client.post("/api/login", json={
        "email": "student@cst.edu.bt",
        "password": "wrongpassword"
    })
    assert res.status_code == 401
    assert res.get_json()["error"] == "Invalid credentials"


def test_login_nonexistent_email(client):
    """Unknown email returns 401 with same message (no user enumeration)."""
    res = client.post("/api/login", json={
        "email": "nobody@cst.edu.bt",
        "password": "password123"
    })
    assert res.status_code == 401
    assert res.get_json()["error"] == "Invalid credentials"


def test_login_missing_email(client):
    """Missing email returns 400."""
    res = client.post("/api/login", json={"password": "password123"})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_login_missing_password(client):
    """Missing password returns 400."""
    res = client.post("/api/login", json={"email": "student@cst.edu.bt"})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_login_empty_body(client):
    """Empty JSON body returns 400."""
    res = client.post("/api/login", json={})
    assert res.status_code == 400
    assert "error" in res.get_json()


# ============================================================
# SECURITY & CONTRACT CASES
# ============================================================

def test_login_does_not_leak_user_existence(client):
    """Wrong email and wrong password return identical error (prevent enumeration)."""
    res1 = client.post("/api/login", json={
        "email": "nobody@cst.edu.bt",
        "password": "password123"
    })
    res2 = client.post("/api/login", json={
        "email": "student@cst.edu.bt",
        "password": "wrongpassword"
    })
    
    # Both must be 401
    assert res1.status_code == 401
    assert res2.status_code == 401
    
    # Both must have the EXACT same error message
    assert res1.get_json()["error"] == res2.get_json()["error"] == "Invalid credentials"


def test_token_contains_correct_claims(client):
    """JWT decodes to the right user_id and role."""
    from auth.jwt_handler import decode_token
    res = client.post("/api/login", json={
        "email": "student@cst.edu.bt",
        "password": "password123"
    })
    token = res.get_json()["token"]
    payload = decode_token(token)
    assert payload["role"] == "student"
    assert "user_id" in payload
    assert "exp" in payload


def test_login_response_matches_contract(client):
    """Response shape must match docs/api.md exactly (no missing fields)."""
    res = client.post("/api/login", json={
        "email": "student@cst.edu.bt",
        "password": "password123"
    })
    assert res.status_code == 200
    data = res.get_json()

    # Every field from the contract must be present
    required_fields = ["token", "user_id", "name", "role", "year"]
    for field in required_fields:
        assert field in data, f"Missing field in response: {field}"

    # Types must be correct
    assert isinstance(data["token"], str)
    assert isinstance(data["user_id"], int)
    assert isinstance(data["name"], str)
    assert data["role"] in ("student", "faculty", "admin")
