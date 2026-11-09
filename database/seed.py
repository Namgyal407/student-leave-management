"""Populate a demo installation with example users and applications.

Safe by default: existing records are not deleted or overwritten. This script
can be run repeatedly and only creates missing demonstration accounts. Use
--reset ONLY if you intentionally want to erase all saved leave data.
"""
import argparse
import os

import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

TYPES = [
    ("Medical", "Medical appointments, illness, recovery", 30, True),
    ("Personal", "Personal matters", 10, False),
    ("Family", "Family emergencies or events", 15, False),
    ("Academic", "Conferences, competitions, research", 10, True),
    ("Other", "Other reasons, subject to approval", 7, False),
]
USERS = [
    ("Sonam Dorji", "student@cst.edu.bt", "student", "3rd Year", "Computer Science", "17123456"),
    ("Pema Choden", "student2@cst.edu.bt", "student", "Final Year", "Computer Science", "17123457"),
    ("Tashi Wangmo", "student3@cst.edu.bt", "student", "1st Year", "Information Tech", "17123460"),
    ("Dr. Kinley Wangchuk", "faculty@cst.edu.bt", "faculty", None, "Computer Science", "17123458"),
    ("Mr. Ugyen Tshering", "faculty2@cst.edu.bt", "faculty", None, "Information Tech", "17123461"),
    ("Admin User", "admin@cst.edu.bt", "admin", None, "Administration", "17123459"),
]
SAMPLE_LEAVES = [
    ("student@cst.edu.bt", "Medical", "Fever and flu symptoms", "2026-10-10", "2026-10-12"),
    ("student@cst.edu.bt", "Personal", "Family event out of town", "2026-10-20", "2026-10-21"),
    ("student2@cst.edu.bt", "Academic", "Research conference in Thimphu", "2026-11-01", "2026-11-03"),
    ("student2@cst.edu.bt", "Medical", "Dental surgery", "2026-11-10", "2026-11-12"),
    ("student3@cst.edu.bt", "Family", "Family emergency", "2026-10-15", "2026-10-17"),
]


def seed(reset=False):
    # psycopg2 accepts postgresql://, not SQLAlchemy's +psycopg2 driver suffix.
    url = os.getenv("DATABASE_URL", "postgresql://leave_app:leave_app_password@localhost:5432/leave_management")
    url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    conn = psycopg2.connect(url)
    try:
        with conn:
            with conn.cursor() as cur:
                if reset:
                    print("WARNING: Resetting all leave data, users and notifications!")
                    cur.execute("TRUNCATE audit_log, notifications, leave_applications, users RESTART IDENTITY CASCADE")
                    cur.execute("TRUNCATE leave_types RESTART IDENTITY CASCADE")
                for name, description, days, required in TYPES:
                    cur.execute("""INSERT INTO leave_types (name, description, max_days, requires_doc)
                                   VALUES (%s,%s,%s,%s) ON CONFLICT (name) DO NOTHING""",
                                (name, description, days, required))
                for name, email, role, year, department, phone in USERS:
                    cur.execute("""INSERT INTO users (name, email, password_hash, role, year, department, phone)
                                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                                   ON CONFLICT (email) DO NOTHING""",
                                (name, email, generate_password_hash("password123", method="pbkdf2:sha256"), role, year, department, phone))
                # Only insert the demonstration leaves if the demo student has no applications.
                # This prevents repeated app starts from duplicating data.
                cur.execute("SELECT id FROM users WHERE email='student@cst.edu.bt'")
                row = cur.fetchone()
                if row:
                    cur.execute("SELECT COUNT(*) FROM leave_applications WHERE student_id=%s", (row[0],))
                    has_original_examples = cur.fetchone()[0] > 0
                else:
                    has_original_examples = True
                if not has_original_examples:
                    for email, type_name, reason, start, end in SAMPLE_LEAVES:
                        cur.execute("""INSERT INTO leave_applications
                                       (student_id, leave_type_id, reason, start_date, end_date)
                                       SELECT u.id, lt.id, %s, %s, %s
                                       FROM users u CROSS JOIN leave_types lt
                                       WHERE u.email=%s AND lt.name=%s""",
                                    (reason, start, end, email, type_name))
        print("[OK] Sample accounts ready. Existing users and applications were preserved.")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate the demo database safely.")
    parser.add_argument("--reset", action="store_true", help="DESTROY existing app data before seeding")
    args = parser.parse_args()
    seed(args.reset)
