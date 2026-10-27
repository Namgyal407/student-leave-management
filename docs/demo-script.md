# Security Documentation

## Overview
This document describes the security architecture of the Student Leave Management System, covering authentication, authorization, data integrity, and known limitations.

---

## 1. Authentication

### 1.1 Password Hashing
**What we use:** PBKDF2-SHA256 (via Werkzeug's `generate_password_hash` and `check_password_hash`).

**Why:**
- Passwords are **never** stored in plain text.
- One-way function: you can hash a password, but you cannot reverse the hash.
- Each password gets a unique random salt automatically, preventing rainbow table attacks.
- PBKDF2 is intentionally slow, making brute-force attacks computationally expensive.

**Where:**
- `backend/auth/password.py`

### 1.2 JWT Tokens
**What we use:** JSON Web Tokens signed with HS256.

**How it works:**
1. User submits email + password to `POST /api/login`.
2. Backend verifies the password hash.
3. Backend generates a JWT containing:
   - `user_id` — identifies the user.
   - `role` — their access level.
   - `exp` — expiry timestamp (24 hours).
4. Frontend stores token in `localStorage`.
5. Frontend sends token in every subsequent request: `Authorization: Bearer <token>`.

**Why JWT:**
- **Stateless** — the server doesn't need to store sessions in memory.
- **Tamper-proof** — any modification invalidates the signature.

---

## 2. Authorization (Role-Based Access Control)

### 2.1 Roles
| Role | Can do | Cannot do |
|------|--------|-----------|
| `student` | Submit leaves, view own leaves | Approve leaves, manage users |
| `faculty` | View all leaves, approve/reject | Submit leaves, manage users |
| `admin` | Manage users, view stats | Approve leaves |

### 2.2 Enforcement
Enforced at **four levels**:
1. **Database** — `CHECK (role IN ('student', 'faculty', 'admin'))`
2. **JWT payload** — role is embedded in the token.
3. **Backend route decorators** — `@role_required` blocks unauthorized roles.
4. **Frontend** — redirects users to the correct dashboard.

### 2.3 Example
```python
@leave_bp.route("/api/leaves/<int:id>/approve", methods=["PUT"])
@role_required("faculty")   # Only faculty can call this
def approve_leave(id):
    ...
