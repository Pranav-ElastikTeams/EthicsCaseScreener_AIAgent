#!/bin/bash
# Startup script for Azure App Service
# Launch the Flask app using gunicorn

exec gunicorn app:app --bind=0.0.0.0:8000 --timeout 600 