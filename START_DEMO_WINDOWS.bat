@echo off
setlocal
cd /d "%~dp0"
echo ====================================================
echo       CST STUDENT LEAVE MANAGEMENT SYSTEM
echo ====================================================
echo.
echo Make sure Docker Desktop is running before continuing.
where docker >nul 2>nul
if errorlevel 1 (
    echo ERROR: Docker not found. Install and start Docker Desktop.
    pause
    exit /b 1
)
docker compose up --build -d
if errorlevel 1 (
    echo.
    echo ERROR: Could not start application.
    echo Check Docker Desktop and see docs\setup.md for fixes.
    pause
    exit /b 1
)
echo.
echo Database and web service started. Browser will open.
echo If the page is not ready, refresh after checking docker compose ps.
timeout /t 4 /nobreak >nul
start "" "http://localhost:5000/"
echo.
echo Student: student@cst.edu.bt   / password123
echo Faculty: faculty@cst.edu.bt   / password123
echo Admin:   admin@cst.edu.bt     / password123
echo.
echo Stop later by running: docker compose down
pause
