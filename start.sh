#!/bin/bash

# Check and install dependencies
if [ -f "/dependencies/python-requirements.txt" ]; then
    echo "Dependency file found, starting to install additional dependencies..."
    uv pip install --system -r /dependencies/python-requirements.txt
fi

# Start FastAPI application
exec uvicorn app.main:app --host 0.0.0.0 --port 8194