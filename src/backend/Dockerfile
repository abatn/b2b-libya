# Libya B2B Platform - Backend Dockerfile
# CPU-basiert, Open-Source, minimal
# Quelle: MENA_B2B_LIBYEN_PHASE1_OPENSOURCE.md

FROM python:3.12-slim

WORKDIR /app

# System-Dependencies (minimal fuer SQLite)
# Quelle: SQLite bentuegt keine externen Libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python-Dependencies
# Quelle: requirements.txt mit versionsfixierten Abhaengigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code
COPY . .

# Expose Port
EXPOSE 8000

# Health Check
# Quelle: Projekt-X-Anforderung
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint: Cache leeren + Server starten
ENTRYPOINT ["sh", "entrypoint.sh"]
