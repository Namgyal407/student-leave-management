# Student Leave Management System

A working full-stack campus leave portal for **students, faculty and administrators** at CST.

## Features

| Student | Faculty | Administrator |
|---|---|---|
| Login, view overview | Login, view departmental overview | Login, view campus-wide overview |
| Submit leave requests and upload evidence | Review students in own department only | See all requests and review them |
| View history, edit pending, cancel eligible leave | Approve/reject with remarks | Add/edit/deactivate user accounts |
| View notifications and change password | View notifications and change password | Configure leave types and password |

**Stack:** Plain HTML/CSS/JavaScript frontend, Flask REST API, SQLAlchemy, PostgreSQL, JWT, Docker Compose, GitHub Actions. No Node/npm installation required.

## Quick start (Docker Desktop recommended)

1. Unzip the project and open PowerShell in the project directory (where `compose.yaml` is).
2. Start Docker Desktop.
3. Run:

   ```powershell
   docker compose up --build -d
   docker compose ps
   ```

4. Open **http://localhost:5000** in your browser. Both the frontend and backend use this address.
5. Sign in using one of these **demonstration accounts**:

   | Role | Email | Password |
   |---|---|---|
   | Student | `student@cst.edu.bt` | `password123` |
   | Faculty (Computer Science) | `faculty@cst.edu.bt` | `password123` |
   | Faculty (Information Tech) | `faculty2@cst.edu.bt` | `password123` |
   | Administrator | `admin@cst.edu.bt` | `password123` |

6. Stop when done with `docker compose down` (retains database and uploads).

**Important:** Keep `compose.yaml`, `Dockerfile`, `backend/`, `frontend/`, and `database/` together. Docker uses a separate database volume and does *not* need or affect your computer's existing PostgreSQL port 5432. `docker compose down -v` permanently deletes demo data and uploads—avoid it unless deliberately resetting.

Detailed instructions, no-Docker alternative and troubleshooting: **[docs/setup.md](docs/setup.md)**.

## Tutor demo sequence

1. Student login → overview → **Apply for leave** → choose *Personal*, future dates and reason → submit.
2. **My applications** → see *Pending*.
3. Sign out → Faculty login (`faculty@cst.edu.bt`) → **Pending approvals** → review → approve with a comment.
4. Sign out → Student login → see *Approved* in history and notification.
5. Sign out → Admin login → **Manage users** and **Leave types**.

## Project structure

```text
frontend/             Login page, responsive dashboards, JavaScript interactions
backend/              Flask APIs, JWT auth, document uploads, ORM models
database/             PostgreSQL schema, safe demo seed script
.github/workflows/    Flask + PostgreSQL automated CI checks
tests/                API/security/integration tests
docs/                 API contract, setup instructions, tutor demo
Dockerfile            Python application image
compose.yaml          Flask + PostgreSQL stack and persisted data
```

## Validation and boundaries

- `GET /api/health` tests database connectivity.
- Run `pytest -q tests` after starting a populated PostgreSQL database.
- See [docs/api.md](docs/api.md) for API endpoints.
- Document uploads: authenticated PDF/JPG/PNG, 5 MB limit, private access checks.
- This is a **local academic demo configuration**, not a production deployment: the included sample password, Compose database password and fallback signing key must be replaced before public hosting; use HTTPS and further security hardening for production.
