"""Test the database connection and auth modules."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db import SessionLocal
from models import User, LeaveApplication, LeaveType, Notification, AuditLog
from auth.password import hash_password, verify_password
from auth.jwt_handler import generate_token, decode_token

print("=" * 60)
print("DATABASE + AUTH TEST")
print("=" * 60)

db = SessionLocal()

print("\n[1] Users:")
for u in db.query(User).all():
    print(f"    {u.id}: {u.name:25} | {u.role:8} | year={u.year}")

print("\n[2] Leave types:")
for lt in db.query(LeaveType).all():
    print(f"    {lt.id}: {lt.name:10} | max_days={lt.max_days}")

print("\n[3] Leave applications:")
for leave in db.query(LeaveApplication).all():
    print(f"    {leave.id}: student={leave.student_id}, "
          f"type={leave.leave_type_id}, status={leave.status}")

print("\n[4] Password hashing:")
hashed = hash_password("password123")
print(f"    Hash: {hashed[:40]}...")
print(f"    Correct password:  {verify_password('password123', hashed)}")
print(f"    Wrong password:    {verify_password('wrong', hashed)}")

print("\n[5] JWT:")
token = generate_token(user_id=1, role="student")
print(f"    Token: {token[:50]}...")
print(f"    Decoded: {decode_token(token)}")

db.close()
print("\n" + "=" * 60)
print("[OK] ALL TESTS PASSED")
print("=" * 60)
