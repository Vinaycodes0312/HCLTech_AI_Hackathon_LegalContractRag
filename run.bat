@echo off
echo Starting Bussiness Contract Search System...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Check if .env exists
if not exist .env (
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and add your Gemini API key.
    echo.
    pause
    exit /b 1
)

REM Create data directories if they don't exist
if not exist data\uploads mkdir data\uploads
if not exist data\faiss_index mkdir data\faiss_index

REM Start the server
echo Server starting at http://localhost:8000
echo API docs at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
