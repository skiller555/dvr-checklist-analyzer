@echo off
title DVR Checklist Analyzer - Avvio
color 0A

echo.
echo  ============================================
echo   DVR Checklist Analyzer - Avvio Server
echo  ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato sul sistema.
    echo Scarica e installa Python da: https://www.python.org/downloads/
    echo Assicurati di spuntare "Add Python to PATH" durante l'installazione.
    echo.
    pause
    exit /b 1
)

echo [1/3] Python trovato. Installazione dipendenze in corso...
echo       (Questo passaggio e' necessario solo al primo avvio)
echo.

pip install flask pymupdf python-docx google-genai --quiet --upgrade
if errorlevel 1 (
    echo.
    echo [ATTENZIONE] Alcune librerie potrebbero non essersi installate.
    echo Prova a eseguire questo file come Amministratore.
    echo.
) else (
    echo [OK] Dipendenze installate correttamente.
)

echo.
echo [2/3] Avvio del server in corso...
echo.
echo  ============================================
echo   APP DISPONIBILE SU:
echo   - Questo PC:    http://localhost:5000
echo   - Rete locale:  http://%COMPUTERNAME%:5000
echo  ============================================
echo.
echo [3/3] Apertura del browser...
echo.
echo [INFO] Chiudi questa finestra per spegnere il server.
echo.

REM Open the browser after a short delay
start "" /min cmd /c "timeout /t 2 >nul && start http://localhost:5000"

REM Start the Flask server
cd /d "%~dp0"
python app.py

echo.
echo Server arrestato.
pause
