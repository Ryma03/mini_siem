@echo off
REM Script de demarrage rapide pour Mini SIEM en mode TEST (Windows)
REM Genere des alertes mock pour tester sans Snort

echo ===============================================================
echo   Mini SIEM - Demarrage en mode TEST (Alertes Mock)
echo ===============================================================
echo.

REM Verifier si Python est installe
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo.
    echo Telechargez Python sur: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detecte
echo.

REM Verifier si les dependances sont installees
echo Verification des dependances...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installation des dependances...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERREUR] Echec de l'installation des dependances
        pause
        exit /b 1
    )
) else (
    echo [OK] Dependances installees
)

echo.
echo ===============================================================
echo   Demarrage de l'application...
echo ===============================================================
echo.

REM Demarrer l'application
python start_test.py

pause
