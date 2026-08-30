# ============================================================
# Libya B2B Platform - Makefile
# Alibaba-model B2B platform commands
# Version: v2.0 | 17.08.2026
# ============================================================

.PHONY: help setup test lint build up down logs clean

# Standard-Ziel
.DEFAULT_GOAL := help

# ============================================================
# HILFE
# ============================================================

help: ## Diese Hilfe anzeigen
	@echo "Libya B2B Platform - Verfuegbare Befehle:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================
# SETUP
# ============================================================

setup: ## Lokales Setup durchfuehren
	@chmod +x setup.sh
	@./setup.sh

docker-setup: ## Docker-Setup durchfuehren
	@chmod +x docker-setup.sh
	@./docker-setup.sh

# ============================================================
# ENTWICKLUNG
# ============================================================

install: ## Abhaengigkeiten installieren
	cd src/backend && pip install -r requirements.txt

dev: ## Backend im Entwicklungsmodus starten
	cd src/backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# ============================================================
# DOCKER
# ============================================================

build: ## Docker-Images bauen
	docker-compose build

up: ## Container starten
	docker-compose up -d

down: ## Container stoppen
	docker-compose down

logs: ## Container-Logs anzeigen
	docker-compose logs -f

ps: ## Container-Status anzeigen
	docker-compose ps

# ============================================================
# PRODUKTION
# ============================================================

prod-build: ## Produktions-Image bauen
	docker-compose -f docker-compose.prod.yml build

prod-up: ## Produktion starten
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Produktion stoppen
	docker-compose -f docker-compose.prod.yml down

# ============================================================
# TESTS & QUALITAET
# ============================================================

test: ## Tests ausfuehren
	cd src/backend && python -m pytest ../tests/ -v --tb=short

test-coverage: ## Tests mit Coverage ausfuehren
	cd src/backend && python -m pytest ../tests/ -v --cov=. --cov-report=html

lint: ## Linting durchfuehren
	cd src/backend && ruff check .

format: ## Code formatieren
	cd src/backend && ruff format .

# ============================================================
# TOOLS
# ============================================================

health: ## Health-Check durchfuehren
	@curl -s http://localhost:8000/health | python3 -m json.tool

monitor: ## Monitoring-Stats anzeigen
	@curl -s http://localhost:8000/api/monitoring/stats | python3 -m json.tool

health-detailed: ## Detaillierter Health-Check
	@curl -s http://localhost:8000/api/monitoring/health-detailed | python3 -m json.tool

logs-monitor: ## Monitoring-Container-Logs
	@docker-compose logs -f healthcheck-monitor

db-init: ## Datenbank initialisieren
	cd src/backend && python3 -c "from main import Base, engine; Base.metadata.create_all(bind=engine); print('DB initialisiert')"

clean: ## Temporaere Dateien loeschen
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf *.egg-info
