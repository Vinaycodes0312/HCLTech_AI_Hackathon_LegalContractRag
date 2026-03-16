@echo off
echo ========================================
echo Bussiness Contract Search System - Setup
echo ========================================
echo.

echo [1/5] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.8+
    pause
    exit /b 1
)
echo.

echo [2/5] Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)
echo.

echo [3/5] Activating virtual environment...
call venv\Scripts\activate
echo.

echo [4/5] Installing dependencies...
pip install -r requirements.txt
echo.

echo [5/5] Setting up directories...
if not exist data\uploads mkdir data\uploads
if not exist data\faiss_index mkdir data\faiss_index
echo.

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Copy .env.example to .env
echo 2. Add your Gemini API key to .env
echo 3. Run: python -m uvicorn app.main:app --reload
echo.
pause
