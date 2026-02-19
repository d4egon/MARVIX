@echo off
title Marvix Launcher - Simple Start
color 0A
cls

echo ================================================
echo   Marvix Launcher
echo ================================================
echo.

set "MARVIX_ROOT=C:\Marvix"
set "CONDA_PATH=%USERPROFILE%\Miniconda3\Scripts\activate.bat"

echo Opening Anaconda Prompt and running Marvix...
start "Marvix - In Env" /D "%MARVIX_ROOT%\scripts" cmd /k "run_in_env.bat"

echo.
echo Done. Look for the new window titled "Marvix - In Env".
echo It will stay open and show every step.
pause