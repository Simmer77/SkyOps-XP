@echo off
REM =============================================================================
REM SkyOps XP -- Native Windows Launcher Script (run.bat)
REM Operations & Real Airline Economy Platform for X-Plane 12
REM =============================================================================
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

cd /d "%~dp0"

set "PORT=8000"
if not "%SKYOPS_PORT%"=="" set "PORT=%SKYOPS_PORT%"

echo ==================================================================
echo   ✈️  SkyOps XP -- Operations & Real Economy for X-Plane 12
echo ==================================================================

REM 1. Detect Python launcher (python or py -3)
set "PYTHON_CMD="
where python >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=python"
if "%PYTHON_CMD%"=="" where py >nul 2>&1 && set "PYTHON_CMD=py -3"

if not "%PYTHON_CMD%"=="" goto :PYTHON_FOUND

echo [ERROR / ERRORE] Python 3 not found on your Windows system.
echo         Download and install Python 3.10+ from https://www.python.org/downloads/
echo         IMPORTANT: Check "Add python.exe to PATH" during installation.
pause
exit /b 1

:PYTHON_FOUND

REM 2. Check or create Virtual Environment (.venv)
if exist ".venv\Scripts\activate.bat" goto :VENV_EXISTS

echo [INFO] Creating Python virtual environment .venv...
call %PYTHON_CMD% -m venv .venv
if errorlevel 1 goto :VENV_ERROR

call ".venv\Scripts\activate.bat"
echo [INFO] Installing required dependencies (FastAPI, Uvicorn, SQLAlchemy)...
call python -m pip install --upgrade pip
call pip install -r backend\requirements.txt
goto :VENV_READY

:VENV_ERROR
echo [ERROR] Failed to create virtual environment .venv.
pause
exit /b 1

:VENV_EXISTS
call ".venv\Scripts\activate.bat"
python -c "import fastapi, uvicorn, sqlalchemy, aiosqlite, pydantic, httpx" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Syncing missing dependencies from backend\requirements.txt...
    call pip install -r backend\requirements.txt
)

:VENV_READY

REM 3. Check pre-built frontend dashboard
if not exist "frontend\dist\index.html" (
    echo [WARNING] Pre-built web dashboard not found in frontend\dist.
    echo           Please ensure frontend\dist was included in your SkyOps-XP package.
)

REM 4. Display local IPv4 addresses for Tablet / Second Monitor / LAN Wi-Fi
echo.
echo ------------------------------------------------------------------
echo   CONNESSIONE LOCALE E TABLET / NETWORK CONNECTIONS:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4"') do (
    set "IP_ADDR=%%a"
    set "IP_ADDR=!IP_ADDR: =!"
    if not "!IP_ADDR!"=="" (
        if not "!IP_ADDR:~0,4!"=="127." (
            echo   -^> Tablet / iPad / Remote PC:  http://!IP_ADDR!:%PORT%
        )
    )
)
echo.
echo   Local PC Browser:   http://127.0.0.1:%PORT%
echo   X-Plane 12 UDP:     127.0.0.1:49000 (Zero Plugins Required!)
echo ------------------------------------------------------------------
echo   Press CTRL+C to stop the platform / Premi CTRL+C per arrestare.
echo ==================================================================
echo.

REM 5. Start Uvicorn server
set "PYTHONPATH=%~dp0backend"
cd backend
call python -m uvicorn skyops_server:skyops_app --host 0.0.0.0 --port %PORT%
pause
