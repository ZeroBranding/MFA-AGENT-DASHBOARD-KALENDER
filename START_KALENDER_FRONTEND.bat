@echo off
echo ========================================
echo    KALENDER FRONTEND STARTEN
echo ========================================
echo.
echo Starte Kalender Frontend auf sicherem Port 8002...
echo.

cd /d "%~dp0MFA\Kalender-Cusor\frontend"

echo Aktueller Pfad: %CD%
echo.
echo Starte Kalender Frontend...
echo.

npm run dev

echo.
echo Kalender Frontend wurde beendet.
pause
