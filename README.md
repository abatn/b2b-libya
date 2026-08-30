# Libya B2B Platform - KI-gestuetzte B2B-Plattform

**Projektversion:** v1.0  
**Stand:** 15. August 2026  
**Budget:** Max. 20 EUR/Monat Hosting  
**Technologie:** 100% Open-Source, CPU-basiert

---

## Beschreibung

Offline-first KI-B2B-Plattform fuer Libyen, basierend auf dem Alibaba-Modell. Die Plattform adressiert die spezifischen Herausforderungen des libyschen Marktes:

- **100% COD** (Cash on Delivery) mit digitalem Tracking
- **Offline-First** fuer 77,4% Stromzugang (World Bank 2024)
- **Arabischer KI-Chatbot** fuer 6,1 Mio. Internetnutzer
- **QR-Code-Tracking** fuer Transparenz trotz Barzahlung

---

## Quick Start

### Backend starten

```bash
cd src/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

API-Dokumentation: http://localhost:8000/docs

### Tests ausfuehren

```bash
pytest tests/ -v
```

### Docker starten

```bash
docker-compose up -d
```

---

## Technologie-Stack

| Komponente | Technologie | Lizenz |
|------------|-------------|--------|
| Frontend | React Native | MIT |
| Backend | FastAPI | MIT |
| DB | SQLite | Public Domain |
| KI: ML | scikit-learn | BSD-3 |
| KI: NLP | bert-base-arabic | Apache 2.0 |
| KI: CV | OpenCV + MobileNet | Apache 2.0 |
| Hosting | OVH VPS | 20 EUR/Monat |

---

## Projektstruktur

```
libya_b2b_platform/
├── src/
│   ├── backend/
│   │   ├── main.py          # FastAPI Backend
│   │   ├── requirements.txt # Dependencies
│   │   ├── Dockerfile       # Docker-Image
│   │   └── .env             # Konfiguration
│   └── frontend/            # React Native (Phase 2)
├── tests/
│   └── test_backend.py      # Backend-Tests
├── docs/                    # Dokumentation
├── docker-compose.yml       # Docker-Compose
├── pyproject.toml           # Projekt-Konfiguration
└── .github/workflows/ci.yml # GitHub Actions
```

---

## API-Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/health` | GET | Health Check |
| `/api/products` | GET/POST | Produkte auflisten/erstellen |
| `/api/products/{id}` | GET/PUT/DELETE | Produkt verwalten |
| `/api/orders` | GET/POST | Bestellungen (COD) |
| `/api/orders/{id}/deliver` | PUT | Lieferung bestaetigen |
| `/api/chat` | POST | KI-Chatbot (Arabisch) |
| `/api/sync/changes` | GET | Delta-Sync |

---

## Lizenz

MIT License - Siehe LICENSE Datei
