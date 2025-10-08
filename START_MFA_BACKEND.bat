@echo off
echo ========================================
echo    MFA BACKEND API STARTEN
echo ========================================
echo.
echo Starte MFA Backend API auf sicherem Port 8004...
echo.

cd /d "%~dp0MFA"

echo Aktueller Pfad: %CD%
echo.
echo Starte uvicorn Server...
echo.

python -m uvicorn api.dashboard_api:app --host 0.0.0.0 --port 8004 --reload

echo.
echo MFA Backend wurde beendet.
pause
