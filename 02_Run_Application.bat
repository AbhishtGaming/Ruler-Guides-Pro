@echo off
REM ============================================================
REM Ruler Guides - Smart Launcher v2.0
REM ============================================================

setlocal enabledelayedexpansion
title Ruler Guides Launcher

REM Check admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cls
color 0B
echo.
echo ============================================================
echo         RULER GUIDES v2.0 - SMART LAUNCHER
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Python not found!
    echo.
    echo Install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION%

REM Dependencies are now handled via installrequirements.bat

REM Launch
echo ============================================================
echo  STARTING APPLICATION...
echo ============================================================
echo.

cd /d "%~dp0"
python src\ruler_guides_pro.py

if errorlevel 1 (
    color 0C
    echo.
    echo [ERROR] Application exited with error
    pause
)

exit /b 0