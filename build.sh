#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies from the root requirements.txt
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run migrations and collectstatic inside the backend folder
echo "Running Django commands..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
cd backend
python manage.py collectstatic --no-input
python manage.py migrate
echo "Build complete."
