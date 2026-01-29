#!/bin/bash

# REST API Simulator Runner
# This script activates the virtual environment and runs the simulator

# Get the script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check and create virtual environment if not exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv "$SCRIPT_DIR/venv"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created successfully"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"

# Install/update requirements if requirements.txt exists
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "📦 Checking requirements..."
    pip install -q -r "$SCRIPT_DIR/requirements.txt"
    if [ $? -eq 0 ]; then
        echo "✅ Requirements installed/updated"
    else
        echo "⚠️  Warning: Some requirements may not have been installed correctly"
    fi
fi

# Check if main.py exists
if [ ! -f "$SCRIPT_DIR/main.py" ]; then
    echo "❌ main.py not found in $SCRIPT_DIR"
    exit 1
fi

# Run the simulator
echo "🚀 Starting REST API Simulator..."
python3 "$SCRIPT_DIR/main.py"
