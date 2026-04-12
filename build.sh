#!/usr/bin/env bash
# exit on error
set -o errexit
set -x  # Enable verbose logging

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run Django commands inside the backend folder
echo "Running migrations..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
cd backend
python manage.py migrate --no-input

echo "Running collectstatic..."
python manage.py collectstatic --no-input

echo "Build complete."
