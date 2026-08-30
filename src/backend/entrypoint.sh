#!/bin/sh
# Clear stale Python bytecode cache to ensure latest .py code is used
find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Start the server
exec uvicorn main:app --host 0.0.0.0 --port 8000
