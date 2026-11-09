"""Non-destructive integration smoke-check for a running demo on localhost:5000.

Run: python scripts/smoke_check.py
This reads sample data but does not create, update or delete records.
"""
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = "http://localhost:5000"


def request(path, *, token=None, payload=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = Request(BASE + path, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    with urlopen(req, timeout=10) as r:
        return r.status, json.load(r)


def check():
    health, response = request("/api/health")
    assert health == 200 and response["status"] == "ok", "Database health check failed"
    print("[OK] PostgreSQL connected and Flask is responding")
    for role, email in [("student", "student@cst.edu.bt"),
                        ("faculty", "faculty@cst.edu.bt"),
                        ("admin", "admin@cst.edu.bt")]:
        status, result = request("/api/login", payload={"email": email, "password": "password123"})
        assert status == 200 and result["user"]["role"] == role, f"{role} login failed"
        token = result["token"]
        for path in ["/api/me", "/api/leaves", "/api/leaves/summary", "/api/notifications", "/api/leave-types"]:
            status, _ = request(path, token=token)
            assert status == 200, f"{role} cannot open {path}"
        if role == "admin":
            for path in ["/api/users", "/api/leave-types?include_inactive=true"]:
                status, _ = request(path, token=token)
                assert status == 200, f"Administrator cannot open {path}"
        print(f"[OK] {role.title()} login, account and data APIs")
    print("\nPASS: Basic API integration checks completed. Try the browser workflow in docs/setup.md.")


if __name__ == "__main__":
    try:
        check()
    except (AssertionError, URLError, HTTPError, KeyError, ValueError) as exc:
        print(f"\nFAILED: {exc}")
        print("Check: docker compose ps; docker compose logs --tail=100 web")
        sys.exit(1)
