# Libya B2B Platform — single service (HTML + API + static, same-origin)
# Context: repo root. Render + CI build this file.

FROM python:3.12-slim

WORKDIR /app

# curl needed for container healthcheck (docker-compose healthcheck uses curl)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY src/backend/requirements.txt ./src/backend/requirements.txt
RUN pip install --no-cache-dir -r src/backend/requirements.txt

COPY src/ ./src/

WORKDIR /app/src/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
