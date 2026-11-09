# API Contract

Base URL: `http://localhost:5000`. All bodies are JSON. Errors are always `{"error": "message"}`.
Protected endpoints need the header `Authorization: Bearer <token>`.

Roles: `student`, `faculty`, `admin`. Faculty only see/review leaves of students in **their own department**; admin sees everything.

## Login

### `POST /api/login`
Authenticate a user and return a JWT.

| Field | Type | Required |
|-------|------|----------|
| email | string | Yes |
| password | string | Yes |

```json
{ "email": "student@cst.edu.bt", "password": "password123" }
```

**200**
```json
{ "token": "<jwt>", "user": { "id": 1, "name": "Sonam Dorji", "email": "student@cst.edu.bt",
  "role": "student", "year": "3rd Year", "department": "Computer Science",
  "phone": "17123456", "is_active": true } }
```
**400** missing fields · **401** invalid email or password · **403** account deactivated

## Account
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/me` | current user → `{"user": {...}}` |
| POST | `/api/me/password` | `{current_password, new_password}` (min 8 chars) |

## Leaves
| Method | Path | Who | Notes |
|--------|------|-----|-------|
| POST | `/api/leaves` | student | `{leave_type_id, reason, start_date, end_date, document_url?}` → 201 |
| GET | `/api/leaves` | all | scoped by role. Query: `status`, `leave_type_id`, `student_id` (staff), `limit`, `offset` → `{leaves, total, limit, offset}` |
| GET | `/api/leaves/summary` | all | counts per status |
| GET | `/api/leaves/<id>` | all | 404 if not visible to you |
| PUT | `/api/leaves/<id>` | student | edit own **pending** leave |
| POST | `/api/leaves/<id>/cancel` | student | own pending, or approved-and-not-started |
| POST | `/api/leaves/<id>/review` | faculty, admin | `{action: "approve"\|"reject", comment}`; comment required to reject |

Rules: dates `YYYY-MM-DD`; `end_date >= start_date`; days ≤ leave type's `max_days`; types with `requires_doc` need `document_url`;
a student can't have overlapping pending/approved leaves (409). Leave objects include `total_days`, `leave_type`, `student_name`, `reviewer_name`, etc.

## Leave types
| Method | Path | Who |
|--------|------|-----|
| GET | `/api/leave-types` | all (active only) |
| POST | `/api/leave-types` | admin — `{name, description?, max_days?, requires_doc?}` |
| PUT | `/api/leave-types/<id>` | admin — same fields + `is_active` |

## Notifications (own only)
| Method | Path |
|--------|------|
| GET | `/api/notifications?unread=true&limit=50` → `{notifications, unread_count}` |
| POST | `/api/notifications/<id>/read` |
| POST | `/api/notifications/read-all` |

## Users (admin)
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/users?role=student` | |
| POST | `/api/users` | `{name, email, password, role, year (students only), department?, phone?}` |
| PUT | `/api/users/<id>` | `name, department, phone, year, is_active, password` |

## Health
`GET /api/health` → `{"status": "ok"}` (checks the DB connection).

## Frontend routes (Flask serves static frontend)

- `GET /` — login page.
- `GET /dashboard` — role-based SPA; JavaScript checks the saved token using `GET /api/me`.
- `GET /static/css/*`, `GET /static/js/*` — frontend assets.

## Supporting documents

- `POST /api/attachments` — **student only**; multipart field `file`, maximum 5 MB, allowed PDF/JPG/PNG; returns `{ "document_url": "/api/attachments/<id>_<uuid>.pdf", "name": "..." }`.
- `GET /api/attachments/<filename>` — authenticated private download; owner student or faculty in owner's department or administrator if file is linked to an application.
- Attach the returned `document_url` to the leave request. Medical/Academic types require an attachment (or an HTTPS supporting link for legacy data).
- `GET /api/leave-types?include_inactive=true` — administrator sees inactive as well as active leave types.
