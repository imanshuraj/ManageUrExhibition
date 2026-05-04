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

echo "Creating media directories..."
mkdir -p media/project_samples media/project_media media/profile_pics media/chat_images media/chat_files media/resumes media/portfolio_images

echo "Build complete."
