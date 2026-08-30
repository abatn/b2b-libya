#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Produkte für restliche 25 Suppliers erstellen
# Libya B2B Platform — KMU-Integration
# ═══════════════════════════════════════════════════════════════

API="http://localhost:8000"
CREATED=0
FAILED=0

register_and_create() {
    local USERNAME=$1
    local BUSINESS=$2
    local SUPPLIER_ID=$3
    shift 3
    
    # Register seller
    REG=$(curl -s -X POST "$API/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$USERNAME\",\"password\":\"pass123\",\"role\":\"seller\",\"business_name\":\"$BUSINESS\"}")
    
    USER_ID=$(echo $REG | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])" 2>/dev/null)
    
    if [ -z "$USER_ID" ]; then
        echo "  ❌ Registration failed for $BUSINESS"
        FAILED=$((FAILED + $#))
        return
    fi
    
    # Login
    curl -s -X POST "$API/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$USERNAME\",\"password\":\"pass123\"}" \
        -c "/tmp/s$SUPPLIER_ID.txt" > /dev/null
    
    # Create products
    for PRODUCT_JSON in "$@"; do
        RESP=$(curl -s -X POST "$API/api/products" \
            -b "/tmp/s$SUPPLIER_ID.txt" \
            -H "Content-Type: application/json" \
            -d "$PRODUCT_JSON")
        
        if echo $RESP | grep -q '"id"'; then
            NAME=$(echo $PRODUCT_JSON | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])" 2>/dev/null)
            PRICE=$(echo $PRODUCT_JSON | python3 -c "import sys,json; print(json.load(sys.stdin)['price'])" 2>/dev/null)
            echo "  ✅ $NAME — $PRICE LYD"
            CREATED=$((CREATED + 1))
        else
            echo "  ❌ Failed to create product"
            FAILED=$((FAILED + 1))
        fi
    done
}

echo "═════════════════════════════════════════════"
echo "Produkte für 25 restliche Suppliers erstellen"
echo "═════════════════════════════════════════════"
echo ""

# ── #6 Lionsgate Industrial (Hardware) ──
echo "=== #6 Lionsgate Industrial ==="
register_and_create "lionsgate_seller" "Lionsgate Industrial" 6 \
    '{"name":"Hex Bolt M10","name_arabic":"برغي سداسي M10","description":"Stainless steel hex bolt M10x30mm","price":2.50,"currency":"LYD","category":"Hardware","stock_quantity":5000,"moq":100}' \
    '{"name":"Socket Set 46-Piece","name_arabic":"طقم مفاتيح ربط 46 قطعة","description":"Chrome vanadium socket set","price":120.00,"currency":"LYD","category":"Hardware","stock_quantity":30,"moq":2}' \
    '{"name":"Lock washer M8","name_arabic":"غطاء قفل M8","description":"Spring lock washer M8 zinc plated","price":0.80,"currency":"LYD","category":"Hardware","stock_quantity":10000,"moq":500}' \
    '{"name":"Adjustable Wrench 12 inch","name_arabic":"مفتاح ربط قابل للتعديل 12 بوصة","description":"Heavy duty adjustable wrench","price":45.00,"currency":"LYD","category":"Hardware","stock_quantity":40,"moq":2}'
echo ""

# ── #7 Global Tech (IT Equipment) ──
echo "=== #7 Global Tech ==="
register_and_create "globaltech_seller" "Global Tech" 7 \
    '{"name":"Desktop Computer i5","name_arabic":"كمبيوتر مكتبي i5","description":"Intel Core i5 12th Gen desktop","price":2800.00,"currency":"LYD","category":"IT Equipment","stock_quantity":15,"moq":1}' \
    '{"name":"24 inch Monitor","name_arabic":"شاشة 24 بوصة","description":"Full HD IPS monitor 24 inch","price":650.00,"currency":"LYD","category":"IT Equipment","stock_quantity":25,"moq":1}' \
    '{"name":"WiFi Router Dual Band","name_arabic":"راوتر واي فاي ثنائي النطاق","description":"AC1200 dual band WiFi router","price":180.00,"currency":"LYD","category":"IT Equipment","stock_quantity":40,"moq":2}' \
    '{"name":"USB Keyboard + Mouse","name_arabic":"لوحة مفاتيح + فأرة USB","description":"Wired USB keyboard and mouse combo","price":65.00,"currency":"LYD","category":"IT Equipment","stock_quantity":100,"moq":5}'
echo ""

# ── #8 AlKufrah Safety (Safety Equipment) ──
echo "=== #8 AlKufrah Safety ==="
register_and_create "alkufrah_seller" "AlKufrah Safety" 8 \
    '{"name":"Safety Helmet White","name_arabic":"خوذة سلامة بيضاء","description":"Industrial safety helmet EN397","price":35.00,"currency":"LYD","category":"Safety Equipment","stock_quantity":200,"moq":5}' \
    '{"name":"Fire Extinguisher 6kg","name_arabic":"طفاية حريق 6 كجم","description":"ABC powder fire extinguisher 6kg","price":120.00,"currency":"LYD","category":"Safety Equipment","stock_quantity":50,"moq":1}' \
    '{"name":"Safety Goggles","name_arabic":"نظارات سلامة","description":"Anti-fog safety goggles EN166","price":15.00,"currency":"LYD","category":"Safety Equipment","stock_quantity":300,"moq":10}' \
    '{"name":"Work Gloves (12 pairs)","name_arabic":"قفازات عمل (12 زوج)","description":"Cut-resistant work gloves","price":85.00,"currency":"LYD","category":"Safety Equipment","stock_quantity":100,"moq":5}'
echo ""

# ── #9 Libo Safety (Safety Equipment) ──
echo "=== #9 Libo Safety ==="
register_and_create "libo_seller" "Libo Safety" 9 \
    '{"name":"Hi-Vis Vest Orange","name_arabic":"سترة عاكسة برتقالية","description":"High visibility safety vest Class 2","price":25.00,"currency":"LYD","category":"Safety Equipment","stock_quantity":150,"moq":10}' \
    '{"name":"Steel Toe Boots","name_arabic":"حذاء رأس فولاذي","description":"Safety boots with steel toe cap","price":180.00,"currency":"LYD","category":"Safety Equipment","stock_quantity":60,"moq":2}' \
    '{"name":"Ear Plugs (200 pairs)","name_arabic":"سدادات أذن (200 زوج)","description":"Foam ear plugs disposable","price":45.00,"currency":"LYD","category":"Safety Equipment","stock_quantity":80,"moq":5}' \
    '{"name":"Dust Mask N95 (50 pcs)","name_arabic":"قناع غبار N95 (50 قطعة)","description":"N95 particulate respirator mask","price":75.00,"currency":"LYD","category":"Safety Equipment","stock_quantity":100,"moq":5}'
echo ""

# ── #10 ART Libya (Machinery) ──
echo "=== #10 ART Libya ==="
register_and_create "artlibya_seller" "ART Libya" 10 \
    '{"name":"Air Compressor 50L","name_arabic":"compressor هوائي 50 لتر","description":"Portable air compressor 50L 2HP","price":950.00,"currency":"LYD","category":"Machinery","stock_quantity":10,"moq":1}' \
    '{"name":"Water Pump 1HP","name_arabic":"مضخة مياه 1 حصان","description":"Centrifugal water pump 1HP","price":420.00,"currency":"LYD","category":"Machinery","stock_quantity":20,"moq":1}' \
    '{"name":"Jack Hammer Electric","name_arabic":"مطرقة كهربائية","description":"Electric demolition jack hammer 1500W","price":1800.00,"currency":"LYD","category":"Machinery","stock_quantity":5,"moq":1}' \
    '{"name":"Concrete Mixer 350L","name_arabic":"خلاط خرسانة 350 لتر","description":"Electric concrete mixer 350L","price":2200.00,"currency":"LYD","category":"Machinery","stock_quantity":3,"moq":1}'
echo ""

# ── #11 Pochette Pack (Packaging) ──
echo "=== #11 Pochette Pack ==="
register_and_create "pochette_seller" "Pochette Pack" 11 \
    '{"name":"Corrugated Box 40x30x30","name_arabic":"كرتون مموج 40x30x30","description":"Single wall corrugated cardboard box","price":4.50,"currency":"LYD","category":"Packaging","stock_quantity":2000,"moq":100}' \
    '{"name":"Stretch Film 500mm","name_arabic":"فيلم تغليف 500 ملم","description":"Cast stretch film 500mm x 300m","price":35.00,"currency":"LYD","category":"Packaging","stock_quantity":100,"moq":10}' \
    '{"name":"Packing Tape (6 rolls)","name_arabic":"شريط تغليف (6 رولات)","description":"BOPP packing tape 48mm x 100m","price":18.00,"currency":"LYD","category":"Packaging","stock_quantity":200,"moq":20}' \
    '{"name":"Paper Bag Large","name_arabic":"كيس ورق كبير","description":"Kraft paper bag 30x40x12cm","price":1.20,"currency":"LYD","category":"Packaging","stock_quantity":5000,"moq":500}'
echo ""

# ── #12 F A J Trading (Electrical) ──
echo "=== #12 F A J Trading ==="
register_and_create "faj_seller" "F A J Trading" 12 \
    '{"name":"Power Strip 4-Way","name_arabic":"فرشاة كهربائية 4 مخارج","description":"4-gang power strip with surge protection","price":28.00,"currency":"LYD","category":"Electrical","stock_quantity":100,"moq":5}' \
    '{"name":"Extension Cable 25m","name_arabic":"سلك تمديد 25 متر","description":"Heavy duty extension cable 25m","price":85.00,"currency":"LYD","category":"Electrical","stock_quantity":50,"moq":2}' \
    '{"name":"LED Bulb 15W (Pack 10)","name_arabic":"لمبة LED 15 واط (10 حبات)","description":"LED bulb E27 15W 6500K daylight","price":55.00,"currency":"LYD","category":"Electrical","stock_quantity":200,"moq":10}' \
    '{"name":"Junction Box IP65","name_arabic":"صندوق وصلة IP65","description":"Waterproof junction box IP65","price":12.00,"currency":"LYD","category":"Electrical","stock_quantity":150,"moq":10}'
echo ""

# ── #13 Libya Al-Tashyid (Building Materials) ──
echo "=== #13 Libya Al-Tashyid ==="
register_and_create "tashyid_seller" "Libya Al-Tashyid" 13 \
    '{"name":"Red Brick (1000 pcs)","name_arabic":"طوب أحمر (1000 قطعة)","description":"Standard red clay brick","price":350.00,"currency":"LYD","category":"Building Materials","stock_quantity":50,"moq":1}' \
    '{"name":"Gypsum Board 120x240cm","name_arabic":"لوح جبس 120x240 سم","description":"Standard gypsum plasterboard 12.5mm","price":42.00,"currency":"LYD","category":"Building Materials","stock_quantity":200,"moq":10}' \
    '{"name":"Aluminum Window Frame","name_arabic":"إطار نافذة ألومنيوم","description":"Aluminum window frame 120x100cm","price":280.00,"currency":"LYD","category":"Building Materials","stock_quantity":30,"moq":1}' \
    '{"name":"Marble Tile 60x60","name_arabic":"بلاط رخام 60x60","description":"Polished marble floor tile","price":85.00,"currency":"LYD","category":"Building Materials","stock_quantity":100,"moq":10}'
echo ""

# ── #14 Libyan Construction (Building Materials) ──
echo "=== #14 Libyan Construction ==="
register_and_create "libyancon_seller" "Libyan Construction Company" 14 \
    '{"name":"Ready-Mix Concrete (m3)","name_arabic":"خرسانة جاهزة (م3)","description":"Ready-mix concrete C25 grade","price":180.00,"currency":"LYD","category":"Building Materials","stock_quantity":100,"moq":1}' \
    '{"name":"Wood Plank 5x10cm","name_arabic":"خشب لوح 5x10 سم","description":"Treated pine wood plank 3m","price":25.00,"currency":"LYD","category":"Building Materials","stock_quantity":500,"moq":20}' \
    '{"name":"Sand Gravel Mix (Ton)","name_arabic":"خلط رمل وحصى (طن)","description":"Construction sand gravel mix","price":45.00,"currency":"LYD","category":"Building Materials","stock_quantity":200,"moq":5}' \
    '{"name":"Waterproofing Membrane","name_arabic":"شاء waterproof","description":"Bitumen waterproofing membrane 4mm","price":55.00,"currency":"LYD","category":"Building Materials","stock_quantity":80,"moq":10}'
echo ""

# ── #15 Al-Hawari Food (Food & Beverage) ──
echo "=== #15 Al-Hawari Food ==="
register_and_create "hawari_seller" "Al-Hawari Food Stuff" 15 \
    '{"name":"Cooking Oil 5L","name_arabic":"زيت طبخ 5 لتر","description":"Sunflower cooking oil 5L","price":38.00,"currency":"LYD","category":"Food & Beverage","stock_quantity":100,"moq":5}' \
    '{"name":"Rice Basmati 25kg","name_arabic":"أرز بسمتي 25 كجم","description":"Premium basmati rice 25kg bag","price":120.00,"currency":"LYD","category":"Food & Beverage","stock_quantity":50,"moq":2}' \
    '{"name":"Canned Beans (48 cans)","name_arabic":"فاصوليا معلبة (48 علبة)","description":"White beans in tomato sauce 400g","price":95.00,"currency":"LYD","category":"Food & Beverage","stock_quantity":30,"moq":1}' \
    '{"name":"Sugar 50kg","name_arabic":"سكر 50 كجم","description":"Refined white sugar 50kg","price":85.00,"currency":"LYD","category":"Food & Beverage","stock_quantity":60,"moq":2}'
echo ""

# ── #16 Libya Automotive (Automotive) ──
echo "=== #16 Libya Automotive ==="
register_and_create "libyaauto_seller" "Libya Automotive" 16 \
    '{"name":"Engine Oil 5W-40 4L","name_arabic":"زيت محرك 5W-40 4 لتر","description":"Synthetic engine oil 5W-40 4L","price":120.00,"currency":"LYD","category":"Automotive","stock_quantity":80,"moq":2}' \
    '{"name":"Car Battery 12V 74Ah","name_arabic":"بطارية سيارة 12 فولت 74 أمبير","description":"Maintenance-free car battery 12V 74Ah","price":280.00,"currency":"LYD","category":"Automotive","stock_quantity":30,"moq":1}' \
    '{"name":"Brake Pads Front","name_arabic":"باديات فرامل أمامية","description":"Ceramic brake pads front pair","price":95.00,"currency":"LYD","category":"Automotive","stock_quantity":40,"moq":2}' \
    '{"name":"Air Filter Universal","name_arabic":"فلتر هواء يونيفيرسال","description":"Universal car air filter","price":35.00,"currency":"LYD","category":"Automotive","stock_quantity":60,"moq":5}'
echo ""

# ── #17 Mediterranean Textiles (Textiles) ──
echo "=== #17 Mediterranean Textiles ==="
register_and_create "medtextile_seller" "Mediterranean Textiles" 17 \
    '{"name":"Cotton Fabric (per meter)","name_arabic":"قماش قطني (المتر)","description":"100% cotton fabric 1.5m wide","price":18.00,"currency":"LYD","category":"Textiles","stock_quantity":500,"moq":10}' \
    '{"name":"Work Uniform Set","name_arabic":"طقم زي عمل","description":"Industrial work uniform 2-piece","price":120.00,"currency":"LYD","category":"Textiles","stock_quantity":100,"moq":5}' \
    '{"name":"Industrial Towels (50 pcs)","name_arabic":"مناشف صناعية (50 قطعة)","description":"Cotton industrial cleaning towels","price":65.00,"currency":"LYD","category":"Textiles","stock_quantity":80,"moq":10}' \
    '{"name":"Webbing Strap 50mm","name_arabic":"حزام تكييف 50 ملم","description":"Polyester webbing strap 50mm roll","price":45.00,"currency":"LYD","category":"Textiles","stock_quantity":60,"moq":5}'
echo ""

# ── #18 Delta United Co (Packaging) ──
echo "=== #18 Delta United Co ==="
register_and_create "delta_seller" "Delta United Co" 18 \
    '{"name":"Kraft Paper Roll","name_arabic":"لفافة ورق كرافت","description":"Kraft paper roll 100cm x 500m","price":75.00,"currency":"LYD","category":"Packaging","stock_quantity":40,"moq":5}' \
    '{"name":"Shrink Wrap Film","name_arabic":"فيلم shrink wrap","description":"PVC shrink wrap film 30cm roll","price":35.00,"currency":"LYD","category":"Packaging","stock_quantity":60,"moq":10}' \
    '{"name":"Bubble Wrap 1m x 100m","name_arabic":"فقاعات تغليف 1m x 100m","description":"Bubble wrap roll 1m wide 100m","price":55.00,"currency":"LYD","category":"Packaging","stock_quantity":50,"moq":5}' \
    '{"name":"Label Stickers (1000 pcs)","name_arabic":"ملصقات علامات (1000 قطعة)","description":"Printed label stickers 5x3cm","price":25.00,"currency":"LYD","category":"Packaging","stock_quantity":200,"moq":50}'
echo ""

# ── #19 National Cement (Building Materials) ──
echo "=== #19 National Cement ==="
register_and_create "nationalcement_seller" "National Cement Company" 19 \
    '{"name":"OPC Cement 42.5R","name_arabic":"اسمنت بورتلاند عادي 42.5R","description":"Ordinary Portland cement 42.5R 50kg","price":48.00,"currency":"LYD","category":"Building Materials","stock_quantity":500,"moq":20}' \
    '{"name":"White Cement 50kg","name_arabic":"اسمنت أبيض 50 كجم","description":"White Portland cement 50kg","price":65.00,"currency":"LYD","category":"Building Materials","stock_quantity":200,"moq":10}' \
    '{"name":"Cement Mortar 25kg","name_arabic":"ملاط أسمنتي 25 كجم","description":"Pre-mixed cement mortar 25kg","price":32.00,"currency":"LYD","category":"Building Materials","stock_quantity":300,"moq":10}' \
    '{"name":"Grout 5kg","name_arabic":"حشوة 5 كجم","description":"Tile grout 5kg waterproof","price":28.00,"currency":"LYD","category":"Building Materials","stock_quantity":150,"moq":5}'
echo ""

# ── #20 Karmika Global (Machinery) ──
echo "=== #20 Karmika Global ==="
register_and_create "karmika_seller" "Karmika Global" 20 \
    '{"name":"Welding Machine MIG 250A","name_arabic":"جهاز لحام MIG 250 أمبير","description":"MIG welding machine 250A with wire feeder","price":3500.00,"currency":"LYD","category":"Machinery","stock_quantity":5,"moq":1}' \
    '{"name":"Cutting Torch Set","name_arabic":"طقم شعلة قص","description":"Oxy-acetylene cutting torch set","price":450.00,"currency":"LYD","category":"Machinery","stock_quantity":10,"moq":1}' \
    '{"name":"Angle Grinder 230mm","name_arabic":"بلكات 230 ملم","description":"Large angle grinder 230mm 2200W","price":220.00,"currency":"LYD","category":"Machinery","stock_quantity":15,"moq":2}' \
    '{"name":"Electric Drill 13mm","name_arabic":"electric drill 13 ملم","description":"Electric drill 13mm chuck 800W","price":165.00,"currency":"LYD","category":"Machinery","stock_quantity":25,"moq":2}'
echo ""

# ── #21 Al Ebtekar (Chemicals) ──
echo "=== #21 Al Ebtekar ==="
register_and_create "ebtekar_seller" "Al Ebtekar" 21 \
    '{"name":"Industrial Cleaner 5L","name_arabic":"منظف صناعي 5 لتر","description":"Heavy duty industrial cleaner 5L","price":45.00,"currency":"LYD","category":"Chemicals","stock_quantity":80,"moq":5}' \
    '{"name":"Disinfectant 5L","name_arabic":"معقم 5 لتر","description":"Surface disinfectant concentrate 5L","price":55.00,"currency":"LYD","category":"Chemicals","stock_quantity":60,"moq":5}' \
    '{"name":"Hand Sanitizer 5L","name_arabic":"معقم يدين 5 لتر","description":"Alcohol-based hand sanitizer 5L","price":65.00,"currency":"LYD","category":"Chemicals","stock_quantity":50,"moq":2}' \
    '{"name":"Floor Cleaner 5L","name_arabic":"منظف أرضيات 5 لتر","description":"Concentrated floor cleaning solution 5L","price":38.00,"currency":"LYD","category":"Chemicals","stock_quantity":100,"moq":5}'
echo ""

# ── #22 Libyan Fertilisers (Chemicals) ──
echo "=== #22 Libyan Fertilisers ==="
register_and_create "lfertiliser_seller" "Libyan Fertilisers Company" 22 \
    '{"name":"NPK Fertilizer 50kg","name_arabic":"سماد NPK 50 كجم","description":"NPK 15-15-15 fertilizer 50kg","price":95.00,"currency":"LYD","category":"Chemicals","stock_quantity":100,"moq":5}' \
    '{"name":"Urea Fertilizer 50kg","name_arabic":"سماد يوريا 50 كجم","description":"Urea 46% nitrogen fertilizer 50kg","price":75.00,"currency":"LYD","category":"Chemicals","stock_quantity":80,"moq":5}' \
    '{"name":"Organic Compost 25kg","name_arabic":"سماد عضوي 25 كجم","description":"Organic compost soil amendment 25kg","price":45.00,"currency":"LYD","category":"Chemicals","stock_quantity":60,"moq":10}' \
    '{"name":"Micronutrient Mix 5kg","name_arabic":"خلط عناصر دقيقة 5 كجم","description":"Micronutrient fertilizer blend 5kg","price":65.00,"currency":"LYD","category":"Chemicals","stock_quantity":40,"moq":5}'
echo ""

# ── #23 El Meselati Furniture (Furniture) ──
echo "=== #23 El Meselati Furniture ==="
register_and_create "meselati_seller" "El Meselati Furniture" 23 \
    '{"name":"Office Desk 120cm","name_arabic":"مكتب مكتبي 120 سم","description":"Executive office desk 120x60cm","price":350.00,"currency":"LYD","category":"Furniture","stock_quantity":20,"moq":1}' \
    '{"name":"Office Chair Ergonomic","name_arabic":"كرسي مكتبي مريح","description":"Ergonomic office chair with armrests","price":420.00,"currency":"LYD","category":"Furniture","stock_quantity":15,"moq":1}' \
    '{"name":"Filing Cabinet 3-Drawer","name_arabic":"خزانة ملفات 3 درج","description":"Metal filing cabinet 3 drawers","price":280.00,"currency":"LYD","category":"Furniture","stock_quantity":10,"moq":1}' \
    '{"name":"Conference Table 200cm","name_arabic":"طاولة اجتماعات 200 سم","description":"Conference table 200x100cm seats 8","price":850.00,"currency":"LYD","category":"Furniture","stock_quantity":5,"moq":1}'
echo ""

# ── #24 Fares IT Solutions (IT Equipment) ──
echo "=== #24 Fares IT Solutions ==="
register_and_create "faresit_seller" "Fares IT Solutions" 24 \
    '{"name":"Laptop 15.6 inch i5","name_arabic":"لابتوب 15.6 بوصة i5","description":"Laptop Intel i5 8GB RAM 256GB SSD","price":3200.00,"currency":"LYD","category":"IT Equipment","stock_quantity":10,"moq":1}' \
    '{"name":"Network Switch 8-Port","name_arabic":"سويتش شبكة 8 منافذ","description":"Gigabit ethernet switch 8-port","price":120.00,"currency":"LYD","category":"IT Equipment","stock_quantity":30,"moq":2}' \
    '{"name":"Printer Laser Mono","name_arabic":"طابعة ليزر أحادية","description":"Monochrome laser printer USB","price":950.00,"currency":"LYD","category":"IT Equipment","stock_quantity":8,"moq":1}' \
    '{"name":"UPS 1500VA","name_arabic":"UPS 1500 فولت أمبير","description":"Line-interactive UPS 1500VA","price":480.00,"currency":"LYD","category":"IT Equipment","stock_quantity":15,"moq":1}'
echo ""

# ── #25 Al Moheit Computer (IT Equipment) ──
echo "=== #25 Al Moheit Computer ==="
register_and_create "moheit_seller" "Al Moheit Computer" 25 \
    '{"name":"SSD 480GB","name_arabic":"SSD 480 جيجا","description":"SATA SSD 480GB 2.5 inch","price":180.00,"currency":"LYD","category":"IT Equipment","stock_quantity":40,"moq":2}' \
    '{"name":"RAM DDR4 8GB","name_arabic":"RAM DDR4 8 جيجا","description":"DDR4 8GB 2666MHz RAM module","price":120.00,"currency":"LYD","category":"IT Equipment","stock_quantity":50,"moq":2}' \
    '{"name":"Webcam 1080p","name_arabic":"كاميرا ويب 1080p","description":"HD 1080p USB webcam with mic","price":95.00,"currency":"LYD","category":"IT Equipment","stock_quantity":30,"moq":5}' \
    '{"name":"HDMI Cable 3m","name_arabic":"سلك HDMI 3 متر","description":"HDMI 2.0 cable 3m 4K","price":25.00,"currency":"LYD","category":"IT Equipment","stock_quantity":100,"moq":10}'
echo ""

# ── #26 Sahel Alakhdar Flour Mill (Food & Beverage) ──
echo "=== #26 Sahel Alakhdar Flour Mill ==="
register_and_create "sahel_seller" "Sahel Alakhdar Flour Mill" 26 \
    '{"name":"Wheat Flour 50kg","name_arabic":"دقيق قمح 50 كجم","description":"Fine wheat flour 50kg bag","price":65.00,"currency":"LYD","category":"Food & Beverage","stock_quantity":200,"moq":5}' \
    '{"name":"Semolina 25kg","name_arabic":"سميد 25 كجم","description":"Coarse semolina 25kg","price":55.00,"currency":"LYD","category":"Food & Beverage","stock_quantity":100,"moq":5}' \
    '{"name":"Animal Feed 50kg","name_arabic":"علف حيوان 50 كجم","description":"Poultry feed mix 50kg","price":75.00,"currency":"LYD","category":"Food & Beverage","stock_quantity":150,"moq":5}' \
    '{"name":"Bread Flour 25kg","name_arabic":"دقيق خبز 25 كجم","description":"High protein bread flour 25kg","price":48.00,"currency":"LYD","category":"Food & Beverage","stock_quantity":120,"moq":5}'
echo ""

# ── #27 TechnoFarm International (Agriculture) ──
echo "=== #27 TechnoFarm International ==="
register_and_create "technofarm_seller" "TechnoFarm International" 27 \
    '{"name":"Drip Irrigation Kit","name_arabic":"طقم ري بالتنقيط","description":"Drip irrigation system for 100m2","price":250.00,"currency":"LYD","category":"Agriculture","stock_quantity":30,"moq":1}' \
    '{"name":"Sprinkler System","name_arabic":"نظام رشاشات","description":"Impact sprinkler with 30m pipe","price":180.00,"currency":"LYD","category":"Agriculture","stock_quantity":25,"moq":1}' \
    '{"name":"Seeds Variety Pack","name_arabic":"حزمة بذور متنوعة","description":"Mixed vegetable seeds 10 varieties","price":45.00,"currency":"LYD","category":"Agriculture","stock_quantity":50,"moq":5}' \
    '{"name":"Greenhouse Plastic Film","name_arabic":"بلاستيك بيت محمي","description":"UV greenhouse plastic film 6x12m","price":120.00,"currency":"LYD","category":"Agriculture","stock_quantity":20,"moq":2}'
echo ""

# ── #28 Green Libya (Agriculture) ──
echo "=== #28 Green Libya ==="
register_and_create "greenlibya_seller" "Green Libya" 28 \
    '{"name":"Water Pump Solar 12V","name_arabic":"مضخة مياه شمسية 12 فولت","description":"Solar powered water pump 12V 120W","price":380.00,"currency":"LYD","category":"Agriculture","stock_quantity":15,"moq":1}' \
    '{"name":"Sprinkler Head (12 pcs)","name_arabic":"رأس رشاش (12 قطعة)","description":"Adjustable sprinkler head brass","price":55.00,"currency":"LYD","category":"Agriculture","stock_quantity":80,"moq":10}' \
    '{"name":"Pipe 4 inch x 6m","name_arabic":"أنبوب 4 بوصة x 6 متر","description":"PVC irrigation pipe 4 inch 6m","price":35.00,"currency":"LYD","category":"Agriculture","stock_quantity":60,"moq":5}' \
    '{"name":"Water Tank 500L","name_arabic":"خزان مياه 500 لتر","description":"Polyethylene water storage 500L","price":180.00,"currency":"LYD","category":"Agriculture","stock_quantity":20,"moq":1}'
echo ""

# ── #29 Alliance Mechanical (Machinery) ──
echo "=== #29 Alliance Mechanical ==="
register_and_create "alliance_seller" "Alliance Mechanical Equipment" 29 \
    '{"name":"Hydraulic Jack 20T","name_arabic":"جاك هيدروليكي 20 طن","description":"Hydraulic bottle jack 20 ton","price":350.00,"currency":"LYD","category":"Machinery","stock_quantity":10,"moq":1}' \
    '{"name":"Bearing 6205 (10 pcs)","name_arabic":"bearing 6205 (10 قطع)","description":"Deep groove ball bearing 6205","price":85.00,"currency":"LYD","category":"Machinery","stock_quantity":50,"moq":10}' \
    '{"name":"V-Belt B68","name_arabic":"سير ناقل B68","description":"Rubber V-belt B68 inch","price":25.00,"currency":"LYD","category":"Machinery","stock_quantity":80,"moq":10}' \
    '{"name":"Grease Cartridge 400g","name_arabic":"خرطوشة شحم 400 جرام","description":"Multi-purpose grease cartridge 400g","price":12.00,"currency":"LYD","category":"Machinery","stock_quantity":100,"moq":20}'
echo ""

# ── #30 Altazamon Company (Electrical) ──
echo "=== #30 Altazamon Company ==="
register_and_create "altazamon_seller" "Altazamon Company" 30 \
    '{"name":"Distribution Board 18-Way","name_arabic":"لوحة توزيع 18 مفتاح","description":"Metal distribution board 18 way IP43","price":450.00,"currency":"LYD","category":"Electrical","stock_quantity":15,"moq":1}' \
    '{"name":"Contactor 3-Pole 40A","name_arabic":"كونتاكتور 3 قطب 40 أمبير","description":"AC contactor 40A 3-pole 230V","price":180.00,"currency":"LYD","category":"Electrical","stock_quantity":20,"moq":2}' \
    '{"name":"Cable Tray 2m","name_arabic":"صينية كابل 2 متر","description":"Perforated cable tray 2m galvanized","price":65.00,"currency":"LYD","category":"Electrical","stock_quantity":40,"moq":5}' \
    '{"name":"Panel Meter Digital","name_arabic":"جهاز قياس رقمي","description":"Digital panel voltmeter/ammeter","price":95.00,"currency":"LYD","category":"Electrical","stock_quantity":30,"moq":2}'
echo ""

echo "═════════════════════════════════════════════"
echo "ERGEBNIS"
echo "═════════════════════════════════════════════"
echo "  Erstellt: $CREATED Produkte"
echo "  Fehlgeschlagen: $FAILED"
echo "  Erwartet: 100 (25 Supplier × 4 Produkte)"
echo "═════════════════════════════════════════════"
echo ""
echo "=== Verifikation ==="
curl -s http://localhost:8000/api/b2b/stats | python3 -m json.tool
