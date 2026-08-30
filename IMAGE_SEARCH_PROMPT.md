# PROMPT: 312 Echte Produktbilder + 30 Supplier-Logos finden

## AUFGABE
Finde für JEDES der 312 Produkte ein ECHTES Produktfoto und für alle 30 Supplier ein offizielles Firmenlogo.
Das Bild MUSS das Produkt/die Firma zeigen — kein Zufallsfoto.

## PROJEKT
- Pfad: `libya_b2b_platform/src/backend/seed_data.py`
- Dictionaries: `PRODUCT_IMAGES` (312 Einträge) + `SUPPLIER_LOGOS` (30 Einträge)

## REGELN — HART
1. JEDES Produkt braucht sein EIGENES Bild
2. Bild MUSS zum Produkt passen (Portland Cement = Zementfoto, NICHT Essen/Berge/Hunde)
3. Keine Duplikate — jedes Produkt hat einzigartiges Bild
4. URL muss erreichbar sein (curl -I → HTTP 200)
5. Quellen: Hersteller-Website, Amazon, Alibaba, Pexels, Unsplash, Pixabay
6. Bei Supplier-Logos: OFFIZIELLE Firmenlogo-URL von Website/LinkedIn

## VERBOTEN
- Keine Zufallsbilder (picsum, ui-avatars, Google Favicon)
- Kein Bild das nicht zum Produkt passt
- Keine erfundenen Pexels-IDs (nur echte Photo-IDs von echten Seiten)
- Keine Bilder die Copyright verletzen

## ARBEITSABLAUF
Für JEDES Produkt:
1. Web-Suche: `[Produktname] product photo site:pexels.com OR site:unsplash.com OR site:pixabay.com`
2. Nimm den ersten RELEVANTEN Treffer (das Bild muss das Produkt zeigen)
3. Extrahiere die exakte Bild-URL
4. Verifiziere mit curl -I → HTTP 200
5. Trage ein: `"Produktname": "https://..."` in PRODUCT_IMAGES

Für JEDE Supplier:
1. Web-Suche: `[Firmenname] logo official`
2. Nimm das offizielle Logo von Website oder LinkedIn
3. Verifiziere URL
4. Trage ein in SUPPLIER_LOGOS

## KATEGORIEN (312 Produkte)

### Building Materials (32)
Portland Cement 50kg, Steel Rebar 12mm, Ceramic Floor Tiles 60x60, Insulation Board 50mm, White Sand (Ton), Aluminum Window Frame, Cement Mortar 25kg, Plywood Sheet 12mm, Concrete Blocks, Marble Tiles, Drywall Sheets, Roofing Sheets, Adhesive Tile Glue, Silicone Sealant, Wall Plaster 25kg, Steel Pipes Galvanized, Waterproof Membrane, Glass Panel 3mm, PVC Ceiling Panel, Granite Slab, Steel H-Beam 200, Insulation Foam, Wood Door Interior, Aluminum Sliding Door, Concrete Drill Bit Set, Pipe Clamp 2in, Wall Anchor Kit, Grout Tile 25kg, Self-Leveling Compound, Rebar Tie Wire, Waterproof Paint 20L, Floor Leveling Screws

### Electrical (33)
Solar Panel 300W, Copper Cable 2.5mm (100m), Circuit Breaker 32A, LED Flood Light 100W, Diesel Generator 50kVA, Transformer 100kVA, Distribution Panel 12-Way, UPS 3kVA Online, Cable Tray 2m, Wall Switch 1-Gang, Power Socket Outlet, LED Tube Light 1.2m, Electrical Conduit Pipe, Junction Box IP65, Extension Cord 50m, Surge Protector, Solar Inverter 5kW, Battery 200Ah Solar, Cable Gland PG13, MCB Breaker 20A, Cable Lugs 10mm, Extension Board 6-Way, LED Panel 30x30, Cable Conduit 2m, Junction Box Metal, Dimmer Switch, Motion Sensor Light, Generator Oil 10L, Solar Charge Controller, Cable Cutter, Wire Stripper, First Aid Kit Industrial, Emergency Button

### Hardware (15)
Cordless Drill 20V, Angle Grinder 115mm, Welding Machine MMA 200A, Tool Box 3-Tray Metal, Adjustable Wrench 12 inch, Measuring Tape 5m, Hammer Steel 500g, Screwdriver Set 12pc, Socket Set 46pc, Hacksaw Frame, Spirit Level 120cm, Clamp Set 4pc, Drill Bit Set HSS, Pliers Set 5pc, Tape Measure 8m, File Set 10pc

### IT Equipment (15)
Desktop Computer i5, Laptop 15.6 inch, 24" LED Monitor, Network Switch 24-Port, WiFi Router Dual Band, Laser Printer Color, UPS 1kVA, Server Rack 42U, CAT6 Cable 305m, Webcam HD 1080p, USB Keyboard, Wireless Mouse, Monitor Stand, Cable Management Kit, USB Hub 7-Port, Webcam Mount, Screen Protector 24in, Desk Pad XL, Cable Tester, Network Patch Cable 3m

### Machinery (17)
Excavator 20 Ton, Mobile Crane 50 Ton, Concrete Mixer 350L, Compactor Plate 200kg, Air Compressor 100L, Water Pump 3HP, Industrial Boiler, CNC Lathe Machine, Hydraulic Press 100T, Diesel Generator 100kVA, Forklift 3 Ton, Welding Inverter 400A, Angle Iron Cutter, Pipe Threader Manual, Bench Grinder, Drill Press Floor, Sanding Belt Machine, Plasma Cutter 60A

### Food & Beverage (16)
Rice Basmati 25kg, Wheat Flour 50kg, Cooking Oil 18L, Sugar 50kg, Canned Tomatoes 400g, Milk Powder 25kg, Bottled Water 1.5L (24pk), Tea Bags 100pk, Cooking Oil 5L, Tomato Paste 400g, Chickpeas 25kg, Lentils 25kg, Olive Oil 5L, Honey Natural 1kg, Coffee Beans 5kg, Juice Concentrate 5L

### Chemicals (15)
Industrial Detergent 20L, Disinfectant 5L, White Vinegar 5L, Bleach 5L, Hand Sanitizer 500ml, Floor Cleaner Concentrate, Degreaser Industrial, Fertilizer NPK 50kg, Paint Thinner 5L, Epoxy Resin 2kg, Industrial Silicone Sealant, Wood Glue 1L, Rust Remover 1L, Anti-Freeze 5L

### Packaging (13)
Cardboard Box 40x30x30, Bubble Wrap Roll 50m, Packing Tape 48mm, Stretch Film 500mm, Label Sticker Roll, Paper Bag Large, Poly Bag 30x40cm, Strapping Band PP, Foam Sheet 2m, Tissue Paper 1kg, Gift Box Medium, Display Stand Cardboard, Cling Film 300m

### Agriculture (14)
Drip Irrigation Kit, Sprinkler System, NPK Fertilizer 25kg, Seeds Variety Pack, Garden Hose 30m, Water Tank 1000L, Soil pH Meter, Wheelbarrow Heavy Duty, Greenhouse Kit, Tractor Attachments, Compost Bin, Soil Testing Kit, Plant Pots 50pc

### Furniture (8)
Office Desk Executive, Ergonomic Office Chair, Filing Cabinet 4-Drawer, Conference Table, Executive Conference Table, Bookshelf 5-Tier, Filing Cabinet 4-Drawers, Office Sofa 3-Seater, Standing Desk Adjustable

### Safety Equipment (8)
Safety Helmet, Safety Vest Hi-Vis, Work Gloves Leather, Safety Goggles, Fire Extinguisher 6kg, First Aid Kit 50pc, Ear Protection Muffs, Steel Toe Boots

### Plumbing (14)
PVC Pipe 4 inch, Water Tank 500L, Brass Faucet Kitchen, PVC Elbow Connector, PVC Pipe 4in 6m, Water Heater 80L, Toilet Complete Set, Sink Kitchen Steel, Faucet Mixer Kitchen, Shower Set Rain, Pressure Pump 1HP, Water Filter House, Ball Valve 1in Brass, Flexible Hose 1.5m, Drain Cover Steel, Pipe Wrench 18in, Float Valve 1in, Tank Pump 3/4HP, Check Valve 2in

### Textiles (8)
Cotton Fabric Roll 50m, Industrial Work Wear Set, Canvas Tarpaulin 4x6m, Polypropylene Bags, Work Uniform Set, Safety Helmet High-Vis, Cotton Towel 1kg, Canvas Bag, Work Gloves 100pc

### Automotive (8)
Car Battery 12V 100Ah, Engine Oil 5W-40 4L, Brake Pads Set, Air Filter Universal, Motor Oil 5W30 4L, Brake Pads Front, Car Battery 60Ah, Wiper Blades Pair, Spark Plugs 4pc, Engine Coolant 4L

### Lighting (4)
LED Bulb 12W, Street Light LED 150W, Panel Light 60x60, Emergency Light Battery

### Office Supplies (20)
A4 Copy Paper 500 sheets, Ballpoint Pen Box 50pc, Sticky Notes 100pc, File Folder A4 100pc, Desk Organizer 5-Drawer, Whiteboard 90x120cm, Marker Set 12 Colors, Stapler Heavy Duty, Paper Shredder, Laminator A4, Label Maker, Calculator Desktop, Presentation Pointer, Ring Binder A4, Tape Dispenser, Scissors 8-inch, Paper Clips 1000pc, Rubber Bands 500g, Desk Lamp LED, Ergonomic Chair

### Cleaning (15)
Vacuum Cleaner Industrial, Mop Bucket Wringer, Glass Cleaner 5L, Toilet Cleaner 1L, Trash Bags 100pc, Squeegee Floor 60cm, Microfiber Cloth 50pc, Pressure Washer 2000W, Hand Soap Dispenser, Broom Set 3pc, Cleaning Cart, Paper Towel 30pk, Air Freshener 12pk, Drain Cleaner 1L, Dustpan Brush Set

### Medical Supplies (15)
First Aid Kit Industrial, Disposable Gloves 100, Surgical Mask 50pc, Blood Pressure Monitor, Thermometer Digital, Bandage Roll 10cm, Pulse Oximeter, Stethoscope Pro, Wheelchair Foldable, Medical Bed Manual, IV Stand, Oxygen Concentrator, Nebulizer Machine, Medical Waste Bin, N95 Mask 20pc

### Security (15)
CCTV Camera 4MP, DVR 8-Channel, Fire Extinguisher CO2 6kg, Safe Box Hotel, Access Control Keypad, Motion Sensor Alarm, Door Lock Digital, Metal Detector, Barbed Wire 50m, Safety Vest 50pc, Fence Panel 2.5m, Intercom System, Gate Motor, Cable Lock 1.8m, Emergency Button

### Painting (15)
White Emulsion 20L, Primer Coat 20L, Spray Paint Box 12, Paint Roller Set 10pc, Wall Putty 25kg, Painter Tape 48mm, Sandpaper 100pc, Texture Paint 20L, Paint Spray Gun, Anti-Rust Paint 20L, Wood Stain 5L, Varnish Clear 5L, Paint Brush Set 12pc, Caulk Gun, Color Chart Deck

## SUPPLIER (30) — Offizielle Logos suchen
1. AlSahl Group
2. Al-Nakheel Company
3. Asdaa Libya
4. Northfields
5. Libya Tools
6. Lionsgate Industrial
7. Global Tech
8. AlKufrah Safety
9. Libo Safety
10. ART Libya
11. Pochette Pack
12. F A J Trading
13. Libya Al-Tashyid
14. Libyan Construction Company
15. Al-Hawari Food Stuff
16. Libya Automotive
17. Mediterranean Textiles
18. Delta United Co
19. National Cement Company
20. Karmika Global
21. Altazamon Company
22. Al Ebtekar
23. Libyan Fertilisers Company
24. El Meselati Furniture
25. Sahel Alakhdar Flour Mill
26. TechnoFarm International
27. Green Libya
28. Alliance Mechanical Equipment
29. Fares IT Solutions
30. Al Moheit Computer Services

## OUTPUT
Schreibe die fertige Datei als Python-Dictionary zurück in:
`libya_b2b_platform/src/backend/seed_data.py`

Format:
```python
PRODUCT_IMAGES = {
    "Portland Cement 50kg": "https://images.pexels.com/photos/XXXXXX/pexels-photo-XXXXXX.jpeg?auto=compress&cs=tinysrgb&w=400",
    ...
}

SUPPLIER_LOGOS = {
    "AlSahl Group": "https://...",
    ...
}
```

## VERIFY
Am Ende: `python3 verify_images.py` muss 100% zeigen.
