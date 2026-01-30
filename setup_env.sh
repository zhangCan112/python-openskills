#!/bin/bash
# OpenSkills virtual environment setup script (Linux/Mac)

echo "========================================"
echo "OpenSkills Virtual Environment Setup"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[Error] Python3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "[Check] Python version: $(python3 --version)"

# Check if virtual environment already exists
if [ -d ".venv" ]; then
    echo "[Info] Virtual environment already exists, removing..."
    rm -rf .venv
fi

echo "[1/3] Creating virtual environment..."
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "[Error] Failed to create virtual environment."
    exit 1
fi

echo "[2/3] Activating virtual environment..."
source .venv/bin/activate

echo "[3/3] Installing dependencies..."
pip install -e .
if [ $? -ne 0 ]; then
    echo "[Error] Failed to install dependencies."
    exit 1
fi

echo
echo "========================================"
echo "[Success] Virtual Environment Setup Complete!"
echo "========================================"
echo
echo "Usage:"
echo "  1. Activate virtual environment: source .venv/bin/activate"
echo "  2. Use command: openskills --help"
echo "  3. Deactivate virtual environment: deactivate"
echo