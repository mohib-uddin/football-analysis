@echo off
echo ========================================
echo FieldCoachAI - Core AI API
echo ========================================
echo.
echo Starting FastAPI server...
echo.
echo API will be available at:
echo   - API: http://localhost:8000
echo   - Swagger Docs: http://localhost:8000/docs
echo   - ReDoc: http://localhost:8000/redoc
echo.

cd api
python main.py

