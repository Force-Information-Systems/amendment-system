#!/bin/bash
# Azure App Service startup script for FastAPI backend

echo "Starting Amendment System Backend..."

# Install Python dependencies
echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations if needed
# echo "Running database setup..."
# python -m app.database

# Start the application with gunicorn (production-ready)
echo "Starting Uvicorn server..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
