@echo off
title 360 Photo Operator Setup
echo ===============================
echo   360 Photo Operator Installer
echo ===============================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

:: Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c %0' -Verb RunAs"
    exit /b
)

echo Installing required packages...
pip install -r requirements.txt

echo Running installer...
python installer.py

pause