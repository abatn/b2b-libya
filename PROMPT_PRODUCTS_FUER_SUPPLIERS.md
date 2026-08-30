# Prompt: Produkte für restliche Suppliers erstellen

**Ziel:** Erstelle realistische B2B-Produkte für die 25 verbleibenden Suppliers (ID 6-30) der Libya B2B Platform.

---

## Hintergrund

Die Libya B2B Platform hat 30 importierte Suppliers aus Libyen. Die ersten 5 Suppliers haben bereits Produkte:
- Supplier #1 (AlSahl Group): 5 Produkte (Building Materials)
- Supplier #2 (Al-Nakheel Company): 4 Produkte (Plumbing)
- Supplier #3 (Asdaa Libya): 4 Produkte (Electrical)
- Supplier #4 (Northfields): 4 Produkte (Electrical)
- Supplier #5 (Libya Tools): 4 Produkte (Hardware)

**Aufgabe:** Erstelle für die verbleibenden 25 Suppliers jeweils 3-5 realistische Produkte.

---

## API-Endpoints

### 1. Seller-User registrieren
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"SELLER_NAME","password":"pass123","role":"seller","business_name":"FIRMEN_NAME"}'
```

### 2. Login als Seller
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"SELLER_NAME","password":"pass123"}' \
  -c /tmp/seller_cookie.txt
```

### 3. Produkt erstellen
```bash
curl -X POST http://localhost:8000/api/products \
  -b /tmp/seller_cookie.txt \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Produktname (EN)",
    "name_arabic": "اسم المنتج (AR)",
    "description": "Produktbeschreibung",
    "price": 100.00,
    "currency": "LYD",
    "category": "Kategorie",
    "stock_quantity": 50,
    "moq": 1
  }'
```

---

## Verbleibende Supplier (25 Stück)

| ID | Firma | Kategorie | Stadt | Was她verkauft |
|----|-------|-----------|-------|-------------|
| 6 | Lionsgate Industrial | Hardware | Tripoli | Industriewerkzeuge, Schrauben, Muttern |
| 7 | Global Tech | IT Equipment | Tripoli | Computer, Drucker, Netzwerk |
| 8 | AlKufrah Safety | Safety Equipment | Tripoli | PSA, Feuerlöscher, Helm |
| 9 | Libo Safety | Safety Equipment | Tripoli | Sicherheitskleidung, Warnwesten |
| 10 | ART Libya | Machinery | Tripoli | Industriemaschinen, Pumpen |
| 11 | Pochette Pack | Packaging | Tripoli | Kartons, Etiketten, Folien |
| 12 | F A J Trading | Electrical | Misrata | Kabel, Schalter, Steckdosen |
| 13 | Libya Al-Tashyid | Building Materials | Tripoli | Zement, Stahl, Fliesen |
| 14 | Libyan Construction | Building Materials | Tripoli | Baumaschinen, Werkzeuge |
| 15 | Al-Hawari Food | Food & Beverage | Tripoli | Trockenwaren, Getränke |
| 16 | Libya Automotive | Automotive | Tripoli | Autoteile, Reifen, Öl |
| 17 | Mediterranean Textiles | Textiles | Misrata | Stoffe, Bekleidung |
| 18 | Delta United Co | Packaging | Tripoli | Papier, Karton, Tragetaschen |
| 19 | National Cement | Building Materials | Tripoli | Zement, Beton |
| 20 | Karmika Global | Machinery | Tripoli | Schweißgeräte, Kompressoren |
| 21 | Al Ebtekar | Chemicals | Tripoli | Reinigungsmittel, Chemikalien |
| 22 | Libyan Fertilisers | Chemicals | Tripoli | Düngemittel, Agrarchemie |
| 23 | El Meselati Furniture | Furniture | Tripoli | Büromöbel, Stühle, Tische |
| 24 | Fares IT Solutions | IT Equipment | Tripoli | Software, Hardware, Wartung |
| 25 | Al Moheit Computer | IT Equipment | Tripoli | Computer, Zubehör |
| 26 | Sahel Alakhdar Flour | Food & Beverage | Tripoli | Mehl, Getreide, Futter |
| 27 | TechnoFarm International | Agriculture | Tripoli | Saatgut, Dünger, Bewässerung |
| 28 | Green Libya | Agriculture | Benghazi | Bewässerungssysteme, Pumpen |
| 29 | Alliance Mechanical | Machinery | Tripoli | Hydraulik, Pneumatik |
| 30 | Altazamon Company | Electrical | Algharabooli | Schaltschränke, Verteiler |

---

## Regeln für Produkt-Names

1. **EN + AR:** Jedes Produkt braucht `name` (EN) und `name_arabic` (AR)
2. **Preis in LYD:** Alle Preise in Libyschen Dinar (LYD)
3. **Realistische Preise:** Nicht zu billig, nicht zu teuer (Beispiel: Cement 45 LYD/50kg)
4. **MOQ (Minimum Order Quantity):** Sinnvolle Mengenangabe
5. **Kategorie muss passen:** Muss zur Supplier-Kategorie passen
6. **3-5 Produkte pro Supplier:** Nicht mehr, nicht weniger

---

## Preisbeispiele (aus der Plattform)

| Produkt | Preis | Kategorie |
|---------|-------|-----------|
| Portland Cement 50kg | 45 LYD | Building Materials |
| Steel Rebar 12mm | 320 LYD | Building Materials |
| Solar Panel 300W | 850 LYD | Electrical |
| Diesel Generator 50kVA | 12.500 LYD | Electrical |
| Cordless Drill 20V | 185 LYD | Hardware |
| PVC Pipe 4 inch | 22 LYD | Plumbing |
| Circuit Breaker 32A | 25 LYD | Electrical |
| Welding Machine 200A | 320 LYD | Hardware |

---

## Output-Format

Erstelle für jeden Supplier einen CURL-Befehl:

```bash
# Supplier #6: Lionsgate Industrial
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"lionsgate_seller","password":"pass123"}' \
  -c /tmp/s6.txt > /dev/null

curl -X POST http://localhost:8000/api/products \
  -b /tmp/s6.txt -H "Content-Type: application/json" \
  -d '{"name":"Hex Bolt M10","name_arabic":"برغي سداسي M10","description":"Stainless steel hex bolt M10x30mm","price":2.50,"currency":"LYD","category":"Hardware","stock_quantity":5000,"moq":100}'
```

---

## Verifikation

Nach dem Erstellen aller Produkte:
```bash
# Prüfe Gesamtzahl
curl -s http://localhost:8000/api/b2b/stats | python3 -m json.tool

# Erwartet: total_products >= 125 (25 Supplier × 5 Produkte)
```

---

## Zusammenfassung

| Schritt | Aktion |
|---------|--------|
| 1 | Für jeden Supplier: Seller-User registrieren |
| 2 | Für jeden Supplier: Login + Cookie speichern |
| 3 | Für jeden Supplier: 3-5 Produkte erstellen |
| 4 | Verifikation: Gesamtzahl prüfen |

**Gesamtziel:** 25 Supplier × 5 Produkte = **125 neue Produkte** (Total: 146 Produkte)
