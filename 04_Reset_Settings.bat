@echo off
REM ============================================================
REM Config Cleanup Utility
REM ============================================================

net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cls
color 0E
echo.
echo ============================================================
echo  RULER GUIDES - CONFIG CLEANUP
echo ============================================================
echo.
echo This will delete the config folder and all settings.
echo.
echo Cleaning...

REM Delete config folder
cd /d "%~dp0"
if exist "config" (
    rmdir /s /q "config"
    echo [OK] Config folder deleted
) else (
    echo [INFO] Config folder not found
)

echo.
echo Done!
timeout /t 3 >nul