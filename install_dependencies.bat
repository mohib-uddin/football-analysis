@echo off
echo ========================================
echo Installing FieldCoachAI API Dependencies
echo ========================================
echo.

echo Installing core API dependencies...
py -m pip install fastapi uvicorn[standard] pydantic pydantic-settings python-multipart --quiet

echo Installing OpenAI...
py -m pip install openai --quiet

echo Installing utilities...
py -m pip install python-dotenv requests aiofiles --quiet

echo Installing OpenCV (for video analysis)...
py -m pip install opencv-python --quiet

echo Installing NumPy...
py -m pip install numpy --quiet

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Core dependencies installed. The API can now run.
echo.
echo For full video analysis features, you may also need:
echo   - torch (for YOLOv5 models)
echo   - torchvision
echo.
echo But the API will work for grading and Q&A without these.
echo.
pause

