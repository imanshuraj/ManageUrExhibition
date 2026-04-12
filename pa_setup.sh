#!/bin/bash

# PythonAnywhere Setup Script for ManageUrExhibition
# This script automates the creation of a virtualenv and initial setup.

echo "--- Starting PythonAnywhere Setup ---"

# 1. Create Virtual Environment if it doesn't exist
VENV_NAME="pa_venv"
VENV_PATH="$HOME/.virtualenvs/$VENV_NAME"

if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment: $VENV_NAME..."
    python3 -m venv "$VENV_PATH"
else
    echo "Virtual environment already exists."
fi

# 2. Activate Virtualenv and install dependencies
echo "Installing dependencies..."
source "$VENV_PATH/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
pip install mysqlclient

# 3. Request Database Credentials (will be saved to .env)
if [ ! -f "backend/.env" ]; then
    echo "Enter your MySQL Database Name (e.g., yourusername\$exhibition):"
    read db_name
    echo "Enter your MySQL User (your username):"
    read db_user
    echo "Enter your MySQL Password:"
    read db_pass

    echo "Saving credentials to backend/.env..."
    echo "DB_NAME=$db_name" > backend/.env
    echo "DB_USER=$db_user" >> backend/.env
    echo "DB_PASSWORD=$db_pass" >> backend/.env
    echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')" >> backend/.env
    echo "DEBUG=False" >> backend/.env
fi

# 4. Run Migrations and Collectstatic
echo "Running Django migrations..."
cd backend
python manage.py migrate
python manage.py collectstatic --no-input

echo "--- Setup Complete! ---"
echo "Next Steps:"
echo "1. Go to the 'Web' tab in PythonAnywhere."
echo "2. Add a new web app (Manual configuration)."
echo "3. Set Virtualenv path to: $VENV_PATH"
echo "4. Update your WSGI configuration file."
echo "5. Configure Static Files: URL=/static/, directory=$(pwd)/staticfiles"
echo "6. Reload your app."
