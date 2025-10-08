@echo off
echo ========================================
echo    GCZ DASHBOARD STARTEN
echo ========================================
echo.
echo Starte GCZ Dashboard als Desktop App...
echo.

cd /d "%~dp0GCZ_Dashboard"
echo Aktueller Pfad: %CD%
echo.
echo Starte Dashboard Desktop App...
echo.

npm run dev:electron

echo.
echo Dashboard wurde beendet.
pause
