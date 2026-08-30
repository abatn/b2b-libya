#!/bin/bash
# ============================================================
# Libya B2B Platform - Docker-Setup-Skript
# Projektversion: v1.5 | Stand: 15.08.2026
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}[ERFOLG]${NC} $1"; }
print_error() { echo -e "${RED}[FEHLER]${NC} $1"; }
print_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

echo "=========================================="
echo "  Libya B2B Platform - Docker Setup v1.5"
echo "=========================================="
echo ""

# ============================================================
# SCHRITT 1: Docker pruefen
# ============================================================
print_info "Schritt 1: Docker pruefen..."

if ! command -v docker &> /dev/null; then
    print_error "Docker nicht gefunden! Bitte installieren."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose nicht gefunden! Bitte installieren."
    exit 1
fi

print_success "Docker und Docker Compose gefunden"

# ============================================================
# SCHRITT 2: .env Datei erstellen
# ============================================================
print_info "Schritt 2: Umgebungsvariablen..."

if [ -f ".env" ]; then
    print_info ".env existiert bereits"
else
    cp .env.example .env
    print_success ".env aus .env.example erstellt"
fi

# ============================================================
# SCHRITT 3: Verzeichnisse erstellen
# ============================================================
print_info "Schritt 3: Verzeichnisse erstellen..."

mkdir -p data
mkdir -p logs
print_success "Verzeichnisse erstellt"

# ============================================================
# SCHRITT 4: Images bauen
# ============================================================
print_info "Schritt 4: Docker-Images bauen..."

docker-compose build --no-cache
print_success "Docker-Images gebaut"

# ============================================================
# SCHRITT 5: Container starten
# ============================================================
print_info "Schritt 5: Container starten..."

docker-compose up -d
print_success "Container gestartet"

# ============================================================
# SCHRITT 6: Health-Check
# ============================================================
print_info "Schritt 6: Health-Check..."

sleep 10

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend Health-Check bestanden!"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    print_error "Backend Health-Check fehlgeschlagen!"
    docker-compose logs backend
fi

# ============================================================
# SCHRITT 7: Container-Status
# ============================================================
print_info "Schritt 7: Container-Status..."

docker-compose ps
echo ""

# ============================================================
# ZUSAMMENFASSUNG
# ============================================================
echo ""
echo "=========================================="
echo "  Docker Setup abgeschlossen!"
echo "=========================================="
echo ""
print_info "Backend: http://localhost:8000"
print_info "API-Doku: http://localhost:8000/docs"
print_info "Frontend: http://localhost:3000"
echo ""
print_info "Logs anzeigen: docker-compose logs -f"
print_info "Stoppen: docker-compose down"
echo ""
