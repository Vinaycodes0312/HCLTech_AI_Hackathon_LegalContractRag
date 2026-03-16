#!/bin/bash

echo "Starting Bussiness Contract Search System..."
echo

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "WARNING: .env file not found!"
    echo "Please copy .env.example to .env and add your Gemini API key."
    echo
    exit 1
fi

# Create data directories if they don't exist
mkdir -p data/uploads
mkdir -p data/faiss_index

# Start the server
echo "Server starting at http://localhost:8000"
echo "API docs at http://localhost:8000/docs"
echo
echo "Press Ctrl+C to stop the server"
echo

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
