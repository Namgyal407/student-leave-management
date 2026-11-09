@echo off
cd /d "%~dp0"
echo Stopping the Student Leave Management containers...
docker compose down
echo Saved database records and uploaded files remain intact.
pause
