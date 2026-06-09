@echo off
echo SAM.gov Acquisition Intelligence Agent
echo =======================================

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo Starting server at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.
uvicorn main:app --reload --port 8000
