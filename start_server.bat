@echo off
echo ========================================
echo Starting FieldCoachAI API Server
echo ========================================
echo.

echo Checking Python...
py --version
echo.

echo Starting server from project root...
echo.
echo API will be available at:
echo   - http://localhost:8000
echo   - http://localhost:8000/docs
echo   - http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

cd api
py main.py

pause

