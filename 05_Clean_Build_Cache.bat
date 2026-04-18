@echo off
TITLE Clean Build Cache
COLOR 0E

echo ==========================================================
echo         Ruler Guides Pro - Build Cache Cleanup Tool
echo ==========================================================
echo.
echo Deleting heavy Nuitka compile cache and trash folders...
echo.

IF EXIST "ruler_guides_pro.build" (
    echo [X] Removing ruler_guides_pro.build directory...
    rmdir /S /Q "ruler_guides_pro.build"
)

IF EXIST "ruler_guides_pro.dist" (
    echo [X] Removing ruler_guides_pro.dist directory...
    rmdir /S /Q "ruler_guides_pro.dist"
)

IF EXIST "ruler_guides_pro.onefile-build" (
    echo [X] Removing ruler_guides_pro.onefile-build directory...
    rmdir /S /Q "ruler_guides_pro.onefile-build"
)

IF EXIST "src\__pycache__" (
    echo [X] Removing src\__pycache__ directory...
    rmdir /S /Q "src\__pycache__"
)

IF EXIST "__pycache__" (
    echo [X] Removing root __pycache__ directory...
    rmdir /S /Q "__pycache__"
)

IF EXIST "nuitka-crash-report.xml" (
    echo [X] Removing nuitka-crash-report.xml (generated only on failed builds)...
    del /Q "nuitka-crash-report.xml"
)

echo.
echo ==========================================================
echo Cleanup Successful! Your folder is now clean.
echo (Only your source code and the final .EXE file remain.)
echo ==========================================================
echo.
pause
