@echo off
echo ========================================
echo    GCZ COMPLETE SYSTEM STARTEN
echo ========================================
echo.
echo Starte German Code Zero - Komplettes System...
echo.

echo ========================================
echo 1. STARTE MFA BACKEND API
echo ========================================
echo Starte MFA Backend auf sicherem Port 8004...
start "MFA Backend API" cmd /k "cd /d %~dp0MFA && python -m uvicorn api.dashboard_api:app --host 0.0.0.0 --port 8004 --reload"

timeout /t 3 /nobreak >nul

echo ========================================
echo 2. STARTE KALENDER BACKEND
echo ========================================
echo Starte Kalender Backend auf sicherem Port 8003...
start "Kalender Backend" cmd /k "cd /d %~dp0MFA\Kalender-Cusor\backend && npm run dev"

timeout /t 3 /nobreak >nul

echo ========================================
echo 3. STARTE KALENDER FRONTEND
echo ========================================
echo Starte Kalender Frontend auf sicherem Port 8002...
start "Kalender Frontend" cmd /k "cd /d %~dp0MFA\Kalender-Cusor\frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo ========================================
echo 4. STARTE DASHBOARD DEV SERVER
echo ========================================
echo Starte Dashboard Dev Server auf sicherem Port 8001...
start "Dashboard Dev Server" cmd /k "cd /d %~dp0GCZ_Dashboard && npm run dev"

timeout /t 3 /nobreak >nul

echo ========================================
echo 5. STARTE DASHBOARD DESKTOP APP
echo ========================================
echo Starte GCZ Dashboard als Desktop-App...
start "GCZ Dashboard Desktop" cmd /k "cd /d %~dp0GCZ_Dashboard && npm run dev:electron"

echo.
echo ========================================
echo    GCZ COMPLETE SYSTEM GESTARTET!
echo ========================================
echo.
echo 🚀 Services laufen auf sicheren Ports:
echo.
echo 📊 MFA Backend API:        http://localhost:8004
echo 📅 Kalender Backend:        http://localhost:8003
echo 🌐 Kalender Webseite:       http://localhost:8002
echo 🖥️  Dashboard Dev Server:    http://localhost:8001
echo 💻 Dashboard Desktop App:   Electron Fenster
echo.
echo 🔗 Webhook: Kalender -> Dashboard
echo 📋 Patienten-Terminbuchung: http://localhost:8002
echo.
echo ⚠️  WICHTIG: Starte zuerst Ollama mit: ollama serve
echo.
echo ========================================
echo.
pause
