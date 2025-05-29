#!/bin/bash

# Create database directory if it doesn't exist
mkdir -p /home/site/wwwroot/database

# Set environment variables for Python
export PYTHONPATH=$PYTHONPATH:/home/site/wwwroot

# Start Gunicorn
gunicorn --bind=0.0.0.0:8000 --timeout 600 application:app 