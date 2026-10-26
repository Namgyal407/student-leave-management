import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from app import create_app


@pytest.fixture(scope="session")
def client():
    return create_app().test_client()


def login(client, email, password="password123"):
    r = client.post("/api/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.get_json()
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


@pytest.fixture(scope="session")
def student(client):
    return login(client, "student3@cst.edu.bt")      # 1st Year, Information Tech


@pytest.fixture(scope="session")
def faculty_it(client):
    return login(client, "faculty2@cst.edu.bt")      # Information Tech


@pytest.fixture(scope="session")
def faculty_cs(client):
    return login(client, "faculty@cst.edu.bt")       # Computer Science


@pytest.fixture(scope="session")
def admin(client):
    return login(client, "admin@cst.edu.bt")
