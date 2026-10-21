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