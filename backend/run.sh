#!/bin/bash
# Development runner script

# Set environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install dependencies if needed
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations (if using PostgreSQL)
echo "Running database migrations..."
alembic upgrade head

# Start the server
echo "Starting MoltPedia backend..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload