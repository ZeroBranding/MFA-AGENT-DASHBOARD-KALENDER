@echo off
echo ========================================
echo    KALENDER BACKEND STARTEN
echo ========================================
echo.
echo Starte Kalender Backend auf sicherem Port 8003...
echo.

cd /d "%~dp0MFA\Kalender-Cusor\backend"

echo Aktueller Pfad: %CD%
echo.
echo Prüfe ob dist Ordner existiert...
if not exist "dist" (
    echo dist Ordner nicht gefunden. Führe Build aus...
    echo.
    npm run build
    echo.
)

echo Starte Kalender Backend...
echo.

PORT=8003 npm run dev

echo.
echo Kalender Backend wurde beendet.
pause
