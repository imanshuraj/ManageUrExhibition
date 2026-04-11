#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Run migrations from the backend directory
cd backend
python manage.py collectstatic --no-input
python manage.py migrate

# Automatically create or update admin user on every deploy
python manage.py shell < init_admin.py
