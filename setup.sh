#!/bin/bash
# ============================================================
# Libya B2B Platform - Setup-Skript
# Projektversion: v1.5 | Stand: 15.08.2026
# Fuehrt alle Schritte der Umgebungsvorbereitung aus
# ============================================================

set -e  # Bei Fehler abbrechen

# Farben fuer Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktionen
print_success() { echo -e "${GREEN}[ERFOLG]${NC} $1"; }
print_error() { echo -e "${RED}[FEHLER]${NC} $1"; }
print_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

echo "=========================================="
echo "  Libya B2B Platform - Setup v1.5"
echo "=========================================="
echo ""

# ============================================================
# SCHRITT 1: Voraussetzungen pruefen
# ============================================================
print_info "Schritt 1: Voraussetzungen pruefen..."

# Python pruefen
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    print_success "Python gefunden: $PYTHON_VERSION"
else
    print_error "Python3 nicht gefunden! Bitte installieren."
    exit 1
fi

# pip pruefen
if command -v pip3 &> /dev/null; then
    print_success "pip gefunden"
else
    print_error "pip nicht gefunden! Bitte installieren."
    exit 1
fi

# Docker pruefen (optional)
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version 2>&1)
    print_success "Docker gefunden: $DOCKER_VERSION"
    DOCKER_AVAILABLE=true
else
    print_info "Docker nicht gefunden - nur lokale Entwicklung"
    DOCKER_AVAILABLE=false
fi

# ============================================================
# SCHRITT 2: Virtuelle Umgebung erstellen
# ============================================================
print_info "Schritt 2: Virtuelle Umgebung erstellen..."

VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    print_info "Virtuelle Umgebung existiert bereits"
else
    python3 -m venv $VENV_DIR
    print_success "Virtuelle Umgebung erstellt: $VENV_DIR"
fi

# Aktivieren
source $VENV_DIR/bin/activate
print_success "Virtuelle Umgebung aktiviert"

# ============================================================
# SCHRITT 3: Abhaengigkeiten installieren
# ============================================================
print_info "Schritt 3: Abhaengigkeiten installieren..."

cd src/backend

# pip upgraden
pip install --upgrade pip -q

# Requirements installieren
pip install -r requirements.txt -q
print_success "Backend-Abhaengigkeiten installiert"

cd ../..

# ============================================================
# SCHRITT 4: .env Datei erstellen
# ============================================================
print_info "Schritt 4: Umgebungsvariablen..."

if [ -f ".env" ]; then
    print_info ".env Datei existiert bereits"
else
    cp .env.example .env
    print_success ".env aus .env.example erstellt"
fi

# ============================================================
# SCHRITT 5: Datenbank initialisieren
# ============================================================
print_info "Schritt 5: Datenbank initialisieren..."

cd src/backend

# Python-Skript fuer DB-Init
python3 -c "
from main import Base, engine
Base.metadata.create_all(bind=engine)
print('Datenbank-Tabellen erstellt: products, orders, chat_messages, sync_logs')
"

cd ../..
print_success "Datenbank initialisiert"

# ============================================================
# SCHRITT 6: Testdaten laden
# ============================================================
print_info "Schritt 6: Testdaten laden..."

cd src/backend

python3 -c "
from main import engine, Base, SessionLocal, Product, Order
from datetime import datetime

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Test-Produkte
test_products = [
    Product(name='Baumaterial X', name_arabic='مواد بناء X', price=150.0, currency='LYD', category='Bau', stock_quantity=100),
    Product(name='Kabel Y', name_arabic='كابل Y', price=50.0, currency='LYD', category='Elektro', stock_quantity=200),
    Product(name='Schrauben Z', name_arabic='براغي Z', price=25.0, currency='LYD', category='Hardware', stock_quantity=500),
]

for product in test_products:
    db.add(product)

db.commit()
db.close()
print('3 Test-Produkte geladen')
"

cd ../..
print_success "Testdaten geladen"

# ============================================================
# SCHRITT 7: Health-Check durchfuehren
# ============================================================
print_info "Schritt 7: Health-Check..."

cd src/backend

# Server starten (Hintergrund)
uvicorn main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
sleep 3

# Health-Check
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Health-Check bestanden!"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    print_error "Health-Check fehlgeschlagen!"
fi

# Server stoppen
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

cd ../..
print_success "Health-Check abgeschlossen"

# ============================================================
# SCHRITT 8: Tests ausfuehren
# ============================================================
print_info "Schritt 8: Tests ausfuehren..."

cd src/backend

python3 -m pytest ../tests/ -v --tb=short 2>&1 | tail -20

cd ../..
print_success "Tests abgeschlossen"

# ============================================================
# ZUSAMMENFASSUNG
# ============================================================
echo ""
echo "=========================================="
echo "  Setup abgeschlossen!"
echo "=========================================="
echo ""
print_success "Virtuelle Umgebung: $VENV_DIR"
print_success "Backend: src/backend/"
print_success "Tests: tests/"
print_success "Datenbank: libya_b2b.db"
echo ""
print_info "Starten mit:"
echo "  cd src/backend && uvicorn main:app --reload"
echo ""
print_info "Oder mit Docker:"
echo "  docker-compose up"
echo ""
