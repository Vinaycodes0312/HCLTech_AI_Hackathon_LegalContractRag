#!/bin/bash

echo "========================================"
echo "Bussiness Contract Search System - Setup"
echo "========================================"
echo

echo "[1/5] Checking Python installation..."
python3 --version || python --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python not found! Please install Python 3.8+"
    exit 1
fi
echo

echo "[2/5] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv || python -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi
echo

echo "[3/5] Activating virtual environment..."
source venv/bin/activate
echo

echo "[4/5] Installing dependencies..."
pip install -r requirements.txt
echo

echo "[5/5] Setting up directories..."
mkdir -p data/uploads
mkdir -p data/faiss_index
echo

echo "========================================"
echo "Setup complete!"
echo "========================================"
echo
echo "Next steps:"
echo "1. Copy .env.example to .env"
echo "2. Add your Gemini API key to .env"
echo "3. Run: python -m uvicorn app.main:app --reload"
echo
