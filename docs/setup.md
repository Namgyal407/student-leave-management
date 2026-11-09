# Run the complete Student Leave Management System on Windows

## Option A — Docker Desktop (recommended for the tutor demonstration)

### 1. Requirements

- Docker Desktop running (Linux containers)
- Windows PowerShell and a browser
- Your extracted project directory containing `compose.yaml` and `Dockerfile`

**Do not open `frontend/index.html` directly.** Flask serves the frontend and API from the same URL.

### 2. Open PowerShell in the extracted project directory

In File Explorer, open the extracted `student-leave-management` folder, click the address bar, type `powershell`, press Enter.

Check that you can see `compose.yaml`:

```powershell
dir compose.yaml
```

### 3. Build and run

```powershell
docker compose up --build -d
docker compose ps
```

Two containers should be up: `db` (PostgreSQL) and `web` (Flask). The database initializes its tables automatically **on the first run**. Sample users/leaves are inserted safely if absent. Existing records remain when restarting.

Open:

- **Main application:** http://localhost:5000/
- **Database health endpoint:** http://localhost:5000/api/health (should display `{"status":"ok"}`)

Follow startup logs if necessary:

```powershell
docker compose logs -f web
```

Press Ctrl+C to stop watching logs; this leaves the containers running.

### 4. Test accounts

| Role | Email | Password |
|---|---|---|
| Student | `student@cst.edu.bt` | `password123` |
| Student 2 | `student2@cst.edu.bt` | `password123` |
| Student 3 | `student3@cst.edu.bt` | `password123` |
| Faculty — Computer Science | `faculty@cst.edu.bt` | `password123` |
| Faculty — Information Tech | `faculty2@cst.edu.bt` | `password123` |
| Administrator | `admin@cst.edu.bt` | `password123` |

These accounts are for an academic demonstration only. Do not use the demo password for real users.

### 5. Live demonstration (5–7 minutes)

1. Log in as `student@cst.edu.bt`. Open **My applications** to show submitted leave.
2. Click **Apply for leave**, choose *Personal*, select any **future non-overlapping dates**, enter a reason, and submit.
3. Return to **My applications** and show that the new leave is **Pending**.
4. Sign out, log in as `faculty@cst.edu.bt` (the student's department). Open **Pending approvals**, open the new request and **Approve** (or Reject with a mandatory reason).
5. Sign out and log in as the student again. Show the **Approved** status and **Notifications**.
6. Sign out and log in as `admin@cst.edu.bt`. Demonstrate **Manage users** and **Leave types**.
7. Optional: use a medical leave with a PDF document to demonstrate secure evidence uploads.

### 6. Stop and restart later

```powershell
docker compose down          # stop (saved records remain)
docker compose up -d        # start again without rebuilding
```

**Never run** `docker compose down -v` unless you want to destroy all demo PostgreSQL data and uploaded documents. PostgreSQL runs inside Docker and is *not* exposed on the Windows host's port 5432, avoiding conflicts with your previously installed local PostgreSQL server.

### Troubleshooting

| Symptom | Solution |
|---|---|
| `docker` not recognized | Install and open Docker Desktop, then restart PowerShell. |
| Cannot connect to Docker daemon | Start Docker Desktop and wait for its engine to become ready. |
| Port 5000 is already in use | Stop your other Flask process/container using port 5000; then rerun `docker compose up -d`. |
| Browser says unable to connect | Check `docker compose ps` and `docker compose logs web`. |
| `POST /api/login` fails | Check email/password and run `docker compose logs db web`. |
| SQL/schema error | Inspect `docker compose logs db` for initial schema errors. |
| App uses outdated files after changes | Run `docker compose up --build -d` again. |
| Docker image download fails | Docker Desktop must be online for the first Python/PostgreSQL image download. |

To see application logs:

```powershell
docker compose logs --tail=100 web
docker compose logs --tail=100 db
```

## Option B — Python and local PostgreSQL (no Docker)

Use this only if Docker Desktop is unavailable. Requires **Python 3.12 or 3.13**, PostgreSQL 14+, and an existing local PostgreSQL server.

### 1. Create a DB and user (run psql as PostgreSQL admin)

```sql
CREATE USER leave_app WITH PASSWORD 'leave_app_password';
CREATE DATABASE leave_management OWNER leave_app;
```

If the user/database already exists, skip their creation. In psql, run the schema SQL **only once on a fresh database** because `database/schema.sql` drops/recreates tables.

From PowerShell in your project root:

```powershell
psql -h localhost -U leave_app -d leave_management -f database/schema.sql
```

When prompted, type `leave_app_password`.

### 2. Python dependencies and `.env`

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

If Python 3.12 is not installed, use `python -m venv .venv` instead. In `.env`, update `SECRET_KEY` to your own long random string. Ensure `DATABASE_URL` points to your local PostgreSQL database.

### 3. Seed, run, open

```powershell
python database/seed.py
python backend/app.py
```

Leave Flask running. Open http://localhost:5000 in your browser. To stop Flask use Ctrl+C. Run backend tests from another terminal in the root folder using `pytest -q tests` (these tests insert test rows; do not run them against real/private production data).

## API and security notes

- Login sends `POST /api/login`; protected calls use `Authorization: Bearer TOKEN`.
- Student applications are scoped to the authenticated student; faculty only see their own department; admin sees all.
- Uploaded documents are stored under `uploads/` (or a Docker named volume) and authenticated on download.
- Leave statuses are `pending`, `approved`, `rejected`, `cancelled`.
- Sample demo accounts and default secrets in this guide are **not safe for public internet deployment**.
