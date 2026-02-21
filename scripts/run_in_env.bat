@echo off
title Marvix - In Env (Keep This Open)

echo ================================================
echo   Marvix - Running inside Anaconda environment
echo   (this window stays open - watch for errors)
echo ================================================
echo.

set "MARVIX_ROOT=C:\MARVIX"
set "CONDA_PATH=%USERPROFILE%\Miniconda3\Scripts\activate.bat"

echo 1. Activating base environment...
call "%CONDA_PATH%" base
if errorlevel 1 (
    echo ERROR: Failed to activate base. Check path in script.
    pause
    exit /b 1
)
echo OK - base activated.

echo.
echo 2. Activating or creating marvix-env...
conda env list | findstr /C:"marvix-env" >nul
if errorlevel 1 (
    echo Creating marvix-env with Python 3.12...
    conda create -n marvix-env python=3.12 -y
    if errorlevel 1 (
        echo Failed to create env.
        pause
        exit /b 1
    )
)

call conda activate marvix-env
if errorlevel 1 (
    echo Failed to activate marvix-env.
    pause
    exit /b 1
)

echo OK - marvix-env activated.
echo Python version:
python --version

echo.
echo 3. Installing/updating dependencies...
cd /d "%MARVIX_ROOT%\backend"
pip install -r requirements.txt --quiet --upgrade

echo.
echo 4. Starting backend (Flask)...
start "Marvix - Backend" cmd /k "call %CONDA_PATH% base && conda activate marvix-env && cd /d %MARVIX_ROOT%\backend && title Marvix Backend && python jarvis_backend.py"

echo.
echo 5. Waiting 10 seconds for backend...
timeout /t 10 /nobreak >nul

echo.
echo 6. Starting frontend (Electron)...
cd /d "%MARVIX_ROOT%\frontend"
npm start

echo.
echo ================================================
echo BOTH PARTS LAUNCHED!
echo - Backend in separate window
echo - Frontend UI should open now
echo Keep this window open for logs/errors.
pause