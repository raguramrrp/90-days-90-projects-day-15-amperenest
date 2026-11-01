@echo off
setlocal

echo ======================================================================
echo  AmpereNest Automated Test Suite Runner
echo ======================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo Executing automated test suite...
".venv\Scripts\python.exe" manage.py test tests --verbosity=2
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Automated tests encountered errors.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo  [PASS] All 28 automated tests passed successfully!
echo ======================================================================
pause
