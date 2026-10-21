"""
Seed the database with test data.
Run: python database/seed.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from werkzeug.security import generate_password_hash
import psycopg2

DB_CONFIG = {
    "dbname": "leave_management",
    "user": "leave_app",
    "password": "leave_app_password",
    "host": "localhost",
    "port": 5432,
}


def seed():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Clear existing data
    cur.execute("TRUNCATE audit_log, notifications, leave_applications, users RESTART IDENTITY CASCADE;")
    cur.execute("TRUNCATE leave_types RESTART IDENTITY CASCADE;")

    # Leave types
    leave_types = [
        ("Medical",  "Medical appointments, illness, recovery", 30, True),
        ("Personal", "Personal matters",                        10, False),
        ("Family",   "Family emergencies or events",            15, False),
        ("Academic", "Conferences, competitions, research",     10, True),
        ("Other",    "Other reasons, subject to approval",       7, False),
    ]
    for name, desc, max_days, req_doc in leave_types:
        cur.execute(
            """INSERT INTO leave_types (name, description, max_days, requires_doc)
               VALUES (%s, %s, %s, %s)""",
            (name, desc, max_days, req_doc)
        )
    print(f"  Inserted {len(leave_types)} leave types")

    # Users
    users = [
        ("Sonam Dorji",         "student@cst.edu.bt",  "password123", "student", "3rd Year",   "Computer Science", "17123456"),
        ("Pema Choden",         "student2@cst.edu.bt", "password123", "student", "Final Year", "Computer Science", "17123457"),
        ("Tashi Wangmo",        "student3@cst.edu.bt", "password123", "student", "1st Year",   "Information Tech", "17123460"),
        ("Dr. Kinley Wangchuk", "faculty@cst.edu.bt",  "password123", "faculty", None,         "Computer Science", "17123458"),
        ("Mr. Ugyen Tshering",  "faculty2@cst.edu.bt", "password123", "faculty", None,         "Information Tech", "17123461"),
        ("Admin User",          "admin@cst.edu.bt",    "password123", "admin",   None,         "Administration",   "17123459"),
    ]
    for name, email, password, role, year, dept, phone in users:
        cur.execute(
            """INSERT INTO users (name, email, password_hash, role, year, department, phone)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (name, email, generate_password_hash(password), role, year, dept, phone)
        )
        print(f"  Inserted {role:8} {email} (id={cur.fetchone()[0]})")

    # Leaves
    leaves = [
        (1, 1, "Fever and flu symptoms",         "2026-10-10", "2026-10-12"),
        (1, 2, "Family event out of town",       "2026-10-20", "2026-10-21"),
        (2, 4, "Research conference in Thimphu", "2026-11-01", "2026-11-03"),
        (2, 1, "Dental surgery",                 "2026-11-10", "2026-11-12"),
        (3, 3, "Family emergency",               "2026-10-15", "2026-10-17"),
    ]
    for student_id, type_id, reason, start, end in leaves:
        cur.execute(
            """INSERT INTO leave_applications
               (student_id, leave_type_id, reason, start_date, end_date)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (student_id, type_id, reason, start, end)
        )
        print(f"  Inserted leave (id={cur.fetchone()[0]})")

    conn.commit()
    cur.close()
    conn.close()
    print("\n[OK] Database seeded successfully.")


if __name__ == "__main__":
    print("Seeding database...")
    seed()
