@echo off
echo ========================================
echo    GCZ SYSTEM STARTEN
echo ========================================
echo.
echo Starte German Code Zero System...
echo.

echo 1. Starte MFA Backend API...
start "MFA Backend" cmd /k "cd /d %~dp0MFA && python -m uvicorn api.dashboard_api:app --host 0.0.0.0 --port 8004 --reload"

timeout /t 3 /nobreak >nul

echo 2. Starte Kalender Backend...
start "Kalender Backend" cmd /k "cd /d %~dp0MFA\Kalender-Cusor\backend && PORT=8003 npm run dev"

timeout /t 3 /nobreak >nul

echo 3. Starte Kalender Frontend (Online)...
start "Kalender Frontend" cmd /k "cd /d %~dp0MFA\Kalender-Cusor\frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo 4. Starte GCZ Dashboard Desktop App...
start "GCZ Dashboard" cmd /k "cd /d %~dp0GCZ_Dashboard && npm run dev:electron"

echo.
echo ========================================
echo    GCZ SYSTEM GESTARTET!
echo ========================================
echo.
echo Services:
echo - GCZ Dashboard:   Desktop App (Offline)
echo - Kalender:        http://localhost:8002 (Online)
echo - MFA Backend:     http://localhost:8004 (API)
echo - Kalender Backend: http://localhost:8003 (API)
echo.
echo Webhook: Kalender -> Dashboard
echo Vergiss nicht: ollama serve zu starten!
echo.
pause
