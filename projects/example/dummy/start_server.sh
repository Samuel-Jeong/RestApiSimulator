#!/bin/bash
# Start the dummy REST API server

echo "=========================================="
echo "Starting Dummy REST API Server"
echo "=========================================="

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "⚠️  uvicorn not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Start server
echo "🚀 Starting server on http://localhost:7878"
python server.py

