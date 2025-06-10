#!/bin/bash
set -e

echo "Creating virtual environment..."
python -m venv /opt/venv
. /opt/venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Initializing database..."
python init_db.py
python seed_db.py

echo "Build completed successfully!" 