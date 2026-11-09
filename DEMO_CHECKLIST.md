# Tutor demonstration checklist

Before entering the presentation room:

- [ ] Start Docker Desktop and run `docker compose up --build -d` in the project folder.
- [ ] Check `docker compose ps` shows the `web` and `db` containers running.
- [ ] Open `http://localhost:5000/api/health` and confirm `{"status":"ok"}`.
- [ ] Run `python scripts/smoke_check.py` (optional but recommended; does not modify data).
- [ ] Open `http://localhost:5000/` and log in with student account.
- [ ] Have 3 tabs or written login details ready (student, faculty, admin).
- [ ] Choose future leave dates that do not overlap existing demo records.
- [ ] Confirm the demonstration computer is online for the *first Docker build* (images and requirements download), then test once before presenting.

## 5-minute presentation sequence

| Time | Presenter action | What it proves |
|---|---|---|
| 0:00–0:40 | Show login page and sign in as `student@cst.edu.bt` | Authentication and personalized portal |
| 0:40–1:40 | Show overview, create a Personal leave, inspect My applications | Frontend, Flask REST API, PostgreSQL inserts |
| 1:40–2:40 | Sign out, sign in as `faculty@cst.edu.bt`, review/approve new request | Role-based access, departmental scope, approval workflow |
| 2:40–3:20 | Sign in as student and show Approved + Notifications | Database update and in-app notifications |
| 3:20–4:15 | Sign in as `admin@cst.edu.bt`, open Manage users and Leave types | Administrative capabilities |
| 4:15–5:00 | Show health endpoint, Docker containers, CI YAML, briefly explain stack | Full-stack integration and automated tests |

All sample accounts use password `password123` (demo only). For sensitive supporting documents, use a disposable PDF, PNG, or JPEG. Don't upload real medical records while demonstrating.

## Quick Q&A answers

**Why Flask?** A lightweight Python framework exposes JWT-authenticated REST endpoints for three roles.

**Why PostgreSQL?** Relationships between users, leave types, applications, notifications and audit logs need referential integrity and SQL constraints.

**Why Docker Compose?** One command starts an isolated PostgreSQL database and Flask web server consistently on another laptop.

**How is authorization enforced?** Backend tokens are validated and every protected request checks the current active user; faculty access is restricted to their department, while students see their own applications.

**How do approvals work?** A faculty/admin review changes an application status in PostgreSQL; a database trigger records status history and the backend creates a student notification.

**What does GitHub Actions do?** CI starts PostgreSQL, prepares the schema and demo data, runs pytest, and validates frontend JavaScript syntax on commits and PRs.

**Can students upload documents?** Yes; a protected 5 MB PDF/JPG/PNG upload endpoint stores supporting evidence and checks the account/department permissions before download.

## What remains outside this local academic demo

Real institutional SSO, HTTPS deployment, password reset by email, mail/SMS alerts, cloud hosting, data migrations, rate limiting, token revocation and production operations are not configured. The sample users/passwords and Compose defaults are for local presentation only.
