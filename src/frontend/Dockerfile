# Libya B2B Platform - Dockerfile Frontend
# Port 3000 - Python Static Server

FROM python:3.12-slim

WORKDIR /app

# Server-Code kopieren
COPY server.py .
COPY templates/ ./templates/
COPY locales/ ./locales/
COPY static/ ./static/
COPY entrypoint.sh .

# Port exponieren
EXPOSE 3000

# Entrypoint: Cache leeren + Server starten
ENTRYPOINT ["sh", "entrypoint.sh"]
