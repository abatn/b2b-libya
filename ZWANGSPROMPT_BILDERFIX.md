# ZWANGSPROMPT: 100% ECHTE PRODUKTBILDER Pflicht

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  KRITISCHER FEHLER: 0/312 BILDER SIND RICHTIG                             ║
║  STATUS: 312 ZUFALLSBILDER → SOFORTIGE AKTION ERFORDERLICH                ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## VERIFICATION REPORT — AKTUELLER STATUS

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  PRODUCT IMAGES:    0/312 relevant (0%)    ← KATASTROPHAL                  ║
║  HTTP-valid:      312/312 (100%)          ← URLs funktionieren            ║
║  Unique URLs:     312/312 (100%)          ← Keine Duplikate               ║
║  Supplier Logos:   17/30  (57%)           ← 13 Facebook-CDN geblockt     ║
║  Category Images:  20/20  (100%)          ← OK                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### BEISPIELE FÜR FEHLBILDER

| Produkt | Zeigt aktuell | Sollte zeigen |
|---------|---------------|---------------|
| Portland Cement 50kg | Sushi-Rollen | Zement-Sack |
| Steel Rebar 12mm | Biene auf Blume | Stahlbewehrung |
| Ceramic Floor Tiles 60x60 | Internationale Flaggen | Keramikfliesen |
| Solar Panel 300W | Glasmurmeln | Solarpanel |
| Cordless Drill 20V | Unbekannt | Akkubohrer |
| Excavator 20 Ton | Unbekannt | Baugrabenmaschine |

**URSACHE:** Die `PRODUCT_IMAGES` Dictionary use sequenzielle Pexels-Foto-IDs (`106573`, `113341`, etc.) die NICHTS mit den Produktnamen zu tun haben. Das sind generische Stock-Fotos (Essen, Natur, Städte, etc.).

---

## ZWANGSREGELN — KEINE AUSNAHMEN

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  REGEL 1: JEDES BILD MUSS ZUM PRODUKT PASSEN                             ║
║  "Portland Cement" → ZEMENTBILD, kein Essen, keine Natur                  ║
║  "Steel Rebar" → STAHLSTAB, keine Blumen, keine Flaggen                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### VERBOTEN ( Sofortige Abbruch bei Verstoß)

| Verboten | Grund |
|----------|-------|
| ❌ picsum.photos | Zufallsbilder |
| ❌ ui-avatars.com | Generierte Initialen |
| ❌ Google Favicon | 128px Icons |
| ❌ Unpassende Pexels-Fotos | Wie aktuell: Sushi für Zement |
| ❌ Duplikate | Jedes Produkt = eigenes Bild |
| ❌ Unverifizierte URLs | curl -I muss HTTP 200/301/302 zeigen |
| ❌ Platzhalter-Bilder | Kein "coming soon" |

### PFLICHT (Für ALLE 312 Produkte)

| Pflicht | Details |
|---------|---------|
| ✅ ECHTES Produktfoto | Alibaba, Amazon, Hersteller |
| ✅ HTTP-Verifizierung | curl -I → 200/301/302 |
| ✅ Einzigartig | KEIN Duplikat |
| ✅ Relevanz | Bild zeigt das konkrete Produkt |

---

## ARBEITSABLAUF — PFLICHT ERFÜLLEN

### SCHRITT 1: Produktliste laden

```bash
cd /home/batnini/B2B_B2C/libya_b2b_platform
python3 -c "
from src.backend.seed_data import PRODUCTS
for i, p in enumerate(PRODUCTS, 1):
    print(f'{i}. {p[\"name\"]} | {p[\"category\"]}')
print(f'\nGesamt: {len(PRODUCTS)} Produkte')
"
```

### SCHRITT 2: Für JEDES Produkt ein ECHTES Bild suchen

**A) Google Images Suche:**
- Gehe zu `https://www.google.com/search?q={produktname}+product+photo&tbm=isch`
- Oder nutze `web_search` Tool: `"buy {produktname} wholesale product image"`

**B) Bild-URL extrahieren:**
- Nimm das ERSTE relevante Produktbild (KEIN Logo, KEIN Text, KEIN Diagramm)
- Die URL muss auf ein echtes JPEG/PNG Bild zeigen

**C) URL verifizieren:**
```bash
curl -sI "{url}" | head -5
# Muss HTTP 200 oder 301 (Redirect) zeigen
# Content-Type muss image/* sein
```

**D) URL formatieren:**
- Pexels: `https://images.pexels.com/photos/{ID}/pexels-photo-{ID}.jpeg?auto=compress&cs=tinysrgb&w=400`
- Alibaba: `https://img.alicdn.com/imgextra/{path}.jpg`
- Andere: Original-URL mit `?w=400` oder `&width=400` wenn möglich

### SCHRITT 3: Erwartung pro Kategorie

| Kategorie | Produkte | Google-Suchbegriff |
|-----------|----------|-------------------|
| Building Materials | 17 | cement bag, steel rebar, ceramic tiles, drywall, plywood, roofing sheet |
| Electrical | 14 | solar panel, copper cable, circuit breaker, LED flood light, generator, transformer |
| Hardware | 10 | cordless drill, angle grinder, welding machine, tool box, wrench, hammer |
| IT Equipment | 12 | desktop computer, laptop, LED monitor, network switch, WiFi router, laser printer |
| Machinery | 8 | excavator, mobile crane, concrete mixer, air compressor, CNC lathe, forklift |
| Food & Beverage | 16 | rice basmati, wheat flour, cooking oil, sugar, canned tomatoes, milk powder |
| Chemicals | 8 | paint thinner, epoxy resin, silicone sealant, wood glue, rust remover |
| Packaging | 10 | cardboard box, bubble wrap, packing tape, stretch film, paper bag |
| Agriculture | 8 | drip irrigation, sprinkler, fertilizer, seeds, garden hose, water tank |
| Furniture | 8 | office desk, ergonomic chair, filing cabinet, conference table, bookshelf |
| Safety Equipment | 8 | safety helmet, safety vest, work gloves, safety goggles, steel toe boots |
| Plumbing | 6 | PVC pipe, water tank, brass faucet, PVC elbow, drainage pipe |
| Textiles | 4 | cotton fabric, industrial work wear, canvas tarpaulin, polypropylene bags |
| Automotive | 4 | car battery, engine oil, brake pads, air filter |
| Lighting | 4 | LED bulb, street light, panel light, emergency light |
| Office Supplies | 12 | A4 paper, ballpoint pen, sticky notes, whiteboard, stapler, calculator |
| Cleaning | 10 | vacuum cleaner, mop bucket, glass cleaner, pressure washer, broom set |
| Medical Supplies | 12 | blood pressure monitor, thermometer, stethoscope, wheelchair, oxygen concentrator |
| Security | 10 | CCTV camera, DVR, fire extinguisher, safe box, access control |
| Painting | 8 | white emulsion, primer coat, spray paint, paint roller, paint brush |

### SCHRITT 4: Ergebnis in seed_data.py eintragen

Ersetze das `PRODUCT_IMAGES` Dictionary in `src/backend/seed_data.py`:

```python
PRODUCT_IMAGES = {
    "Portland Cement 50kg": "https://images.pexels.com/photos/{NEUE_ID}/...",
    "Steel Rebar 12mm": "https://...",
    # ... für ALLE 312 Produkte
}
```

### SCHRITT 5: Re-Seed + Verifikation

```bash
# 1. Tests ausführen
cd /home/batnini/B2B_B2C/libya_b2b_platform
python3 -m pytest tests/ -v

# 2. Docker rebuild
docker compose up -d --build

# 3. Database re-seed
docker compose exec backend python3 -c "
from seed_data import seed_database
from config import SessionLocal
db = SessionLocal()
seed_database(db)
"

# 4. API prüfen
curl -s "http://localhost:8000/api/products?limit=5" | python3 -m json.tool

# 5. Frontend prüfen
curl -s "http://localhost:3000/b2b/products" | grep -o 'src="[^"]*"' | head -5
```

### SCHRITT 6: Finale Verifikation

```bash
python3 verify_images.py
```

Erwartung:
```
✅ Gültig: 362/362
❌ Ungültig: 0
📊 Quote: 100.0%
🎉 ALLE BILDER SIND GÜLTIG!
```

---

## QUELLEN-FRISTUNG (pro Produkt)

Reihenfolge der Quellen (beste zuerst):

1. **Alibaba.com** — echte Produktbilder von Händlern
2. **Amazon.com** — professionelle Produktfotos
3. **Hersteller-Websites** — offizielle Produktbilder
4. **Google Images** — allgemeine Suche
5. **Pexels.com** — nur wenn Suchbegriff direkt passt (z.B. "cement bag" → Pexels Zement-Bild)

---

## QUALITÄTS-CHECKLISTE

Vor dem Eintragen in `PRODUCT_IMAGES`:

- [ ] Bild zeigt das KONKRETE Produkt (nicht Similar)
- [ ] URL ist erreichbar (curl -I → 200/301/302)
- [ ] Content-Type ist image/*
- [ ] Kein Duplikat mit anderem Produkt
- [ ] Kein Logo, kein Text, kein Diagramm
- [ ] Auflösung mind. 400px breit
- [ ] Kein Watermark (oder nur dezent)

---

## BEISPIELE FÜR RICHTIGE BILDER

| Produkt | Richtige Suche | Erwartetes Bild |
|---------|----------------|-----------------|
| Portland Cement 50kg | "cement bag 50kg product photo" | Zement-Sack mit Markenname |
| Steel Rebar 12mm | "steel rebar 12mm wholesale" | Stahlstab-Stapel |
| Ceramic Floor Tiles 60x60 | "ceramic floor tiles 60x60 product" | Fliesen im Raum |
| Solar Panel 300W | "solar panel 300W product photo" | Solarpanel-Modul |
| Cordless Drill 20V | "cordless drill 20V product" | Akkubohrer mitBOX |
| Excavator 20 Ton | "excavator 20 ton product photo" | Gelbe Baumaschine |

---

## BERICHT AM ENDE

Am Ende muss der Agent einen Bericht vorlegen:

```
═══════════════════════════════════════════════════════════════
  ABSCHLUSSBERICHT — ECHTE PRODUKTBILDER
═══════════════════════════════════════════════════════════════

  Gesamtzahl Produkte:           312
  Bilder verifiziert:            X/312
  Bilder mit echtem Produktfoto: Y/312
  Bilder mit Fallback:           Z/312
  URL-Fehler:                    W/312

  Quellen-Verteilung:
  - Alibaba.com:     A Bilder
  - Amazon.com:      B Bilder
  - Hersteller:      C Bilder
  - Google Images:   D Bilder
  - Pexels (passend): E Bilder

  Kategorie-Status:
  - Building Materials:   17/17 ✅
  - Electrical:           14/14 ✅
  - Hardware:             10/10 ✅
  - IT Equipment:         12/12 ✅
  - Machinery:             8/8  ✅
  - Food & Beverage:      16/16 ✅
  - Chemicals:             8/8  ✅
  - Packaging:            10/10 ✅
  - Agriculture:           8/8  ✅
  - Furniture:             8/8  ✅
  - Safety Equipment:      8/8  ✅
  - Plumbing:              6/6  ✅
  - Textiles:              4/4  ✅
  - Automotive:            4/4  ✅
  - Lighting:              4/4  ✅
  - Office Supplies:      12/12 ✅
  - Cleaning:             10/10 ✅
  - Medical Supplies:     12/12 ✅
  - Security:             10/10 ✅
  - Painting:              8/8  ✅

  Tests: pytest tests/ -v → BESTANDEN
  verify_images.py → 100.0%
═══════════════════════════════════════════════════════════════
```

---

## ZUSAMMENFASSUNG

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  STATUS: 0/312 Bilder korrekt                                             ║
║  ZIEL:   312/312 Bilder korrekt (100%)                                    ║
║  ZEITRAHMEN: SOFORTIGE BEARBEITUNG                                        ║
║  TOLERANZ: 0 Fehler — ALLE müssen passen                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**JEDES PRODUKT MUSS SEIN EIGENES, RELEVANTES BILD HABEN. KEINE AUSNAHMEN.**
