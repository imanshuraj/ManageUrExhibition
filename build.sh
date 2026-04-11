#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies from the root requirements.txt
pip install -r requirements.txt

# Run migrations and collectstatic inside the backend folder
cd backend
python manage.py collectstatic --no-input
python manage.py migrate
