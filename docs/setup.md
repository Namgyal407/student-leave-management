# Local Development Setup

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Git

## Database Setup

```bash
# Create database
psql -U postgres
CREATE DATABASE leave_management;
CREATE USER leave_app WITH PASSWORD 'leave_app_password';
GRANT ALL PRIVILEGES ON DATABASE leave_management TO leave_app;
\q

# Apply schema
psql -U leave_app -d leave_management -f database/schema.sql

# Seed data
python database/seed.py

## Run the backend

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                              # then set SECRET_KEY
cd backend
python app.py                                     # http://localhost:5000
```

Test it:

```bash
curl -i -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@cst.edu.bt","password":"password123"}'

pytest tests            # from the project root; needs the seeded DB (re-run seed.py to reset)
```

Seed accounts (password `password123`): `student@`, `student2@`, `student3@`, `faculty@`, `faculty2@`, `admin@cst.edu.bt`.
