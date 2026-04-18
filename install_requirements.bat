@echo off
title Install Requirements
echo ============================================================
echo      INSTALLING DEPENDENCIES FOR RULER GUIDES PRO 
echo ============================================================
echo.

python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Running pywin32 post-installation scripts (if necessary)...
python -c "import sys, os; sp = os.path.join(sys.prefix, 'Scripts', 'pywin32_postinstall.py'); exec(open(sp).read()) if os.path.exists(sp) else None"

echo.
echo All requirements have been successfully installed!
pause
