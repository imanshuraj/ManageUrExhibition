#!/usr/bin/env bash
# exit on error
set -o errexit
set -x  # Enable verbose logging

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run Django commands inside the backend folder
echo "Running collectstatic..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
cd backend
python manage.py collectstatic --no-input

# Note: Migrations are now handled by the Release Command in Render settings.
# Release Command: cd backend && python manage.py migrate
echo "Build complete."
echo "Build complete."
