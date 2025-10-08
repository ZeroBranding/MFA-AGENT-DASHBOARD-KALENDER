@echo off
echo ========================================
echo    GCZ COMPLETE SYSTEM STARTEN
echo ========================================
echo.
echo Starte German Code Zero - Komplettes System...
echo.

echo 1. Starte MFA Backend API...
start "MFA Backend" cmd /k "cd /d %~dp0MFA && python -m uvicorn api.dashboard_api:app --host 0.0.0.0 --port 8004 --reload"

timeout /t 3 /nobreak >nul

echo 2. Starte Kalender Backend...
start "Kalender Backend" cmd /k "cd /d %~dp0MFA\Kalender-Cusor\backend && npm run dev"

timeout /t 3 /nobreak >nul

echo 3. Starte Kalender Frontend...
start "Kalender Frontend" cmd /k "cd /d %~dp0MFA\Kalender-Cusor\frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo 4. Starte Dashboard Dev Server...
start "Dashboard Dev" cmd /k "cd /d %~dp0GCZ_Dashboard && npm run dev"

timeout /t 3 /nobreak >nul

echo 5. Starte Dashboard Desktop App...
start "GCZ Dashboard" cmd /k "cd /d %~dp0GCZ_Dashboard && npm run dev:electron"

echo.
echo ========================================
echo    GCZ COMPLETE SYSTEM GESTARTET!
echo ========================================
echo.
echo Services:
echo - MFA Backend:      http://localhost:8004
echo - Kalender Backend: http://localhost:8003
echo - Kalender Web:     http://localhost:8002
echo - Dashboard Dev:    http://localhost:8001
echo - Dashboard App:    Desktop Fenster
echo.
echo Webhook: Kalender -> Dashboard
echo.
echo WICHTIG: Starte zuerst ollama serve!
echo.
pause
