#!/bin/bash
set -e

# Default to port 8080 if PORT is not set
PORT=${PORT:-8080}

# Log the port we're using
echo "Starting application on port $PORT"

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT 