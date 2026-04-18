@echo off
title Build Ruler Guides Pro
echo ============================================================
echo   PREPARING COMPILATION ENVIRONMENT FOR RULER GUIDES PRO
echo ============================================================
echo.
echo Installing required Python packages and Nuitka Builder...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install nuitka
python -m pip uninstall -y zstandard

echo.
echo Starting Nuitka Compilation...
echo Note: If a C compiler is missing, it will be automatically downloaded.
echo.

python -m nuitka --onefile --windows-disable-console -o "Ruler Guides Pro.exe" --windows-icon-from-ico=assets\icon.ico --include-data-dir=assets=assets --include-data-files=assets\icon.ico=icon.ico --enable-plugin=pyqt5 --assume-yes-for-downloads --company-name="Abhisht Pandey" --product-name="Ruler Guides Pro" --file-version=3.0.0.0 --product-version=3.0.0.0 --file-description="Professional Screen Ruler and Guide Tool" --copyright="Copyright (C) 2026 Abhisht Pandey. All rights reserved." src\ruler_guides_pro.py

echo.
echo ============================================================
echo Compilation Finished! Check the folder for your EXE.
echo ============================================================
pause
