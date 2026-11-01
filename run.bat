@echo off
setlocal

echo ======================================================================
echo  AmpereNest — Starting Electricity Intelligence Server
echo ======================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo Starting Django development server at:
echo   http://127.0.0.1:8000/
echo.
echo Demo Account:
echo   Username: demouser
echo   Password: demo1234
echo.
echo Press Ctrl+C in this terminal window to stop the server.
echo ======================================================================

".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Server terminated unexpectedly.
    pause
)
