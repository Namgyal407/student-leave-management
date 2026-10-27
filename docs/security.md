# Security Documentation

## Overview

This document describes the security architecture of the Student Leave Management System, covering authentication, authorization, data integrity, and known limitations.

---

## 1. Authentication

### 1.1 Password Hashing

**What we use:** PBKDF2-SHA256 (via Werkzeug's `generate_password_hash` and `check_password_hash`).

**Why:**
- Passwords are **never** stored in plain text
- One-way function: you can hash a password, but you cannot reverse the hash
- Each password gets a unique random salt automatically, preventing rainbow table attacks
- PBKDF2 is intentionally slow, making brute-force attacks computationally expensive

**Where:**
- `backend/auth/password.py`
  ```python
  def hash_password(password: str) -> str:
      return generate_password_hash(password, method='pbkdf2:sha256')

  def verify_password(password: str, password_hash: str) -> bool:
      return check_password_hash(password_hash, password)
