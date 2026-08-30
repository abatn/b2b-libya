#!/usr/bin/env python3
"""
Build PRODUCT_IMAGES mapping using Pexels photo IDs.
Strategy: For each product, construct a Google search query that returns
Pexels photo pages with IDs in the URL. Extract IDs and build mapping.

Image URL format: https://images.pexels.com/photos/{ID}/pexels-photo-{ID}.jpeg?auto=compress&cs=tinysrgb&w=400
"""

import sys
import os
import json
import subprocess
import re
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "backend"))
from seed_data import PRODUCTS

def search_pexels_photo(query, timeout=15):
    """Search Google for a Pexels photo page and extract the photo ID."""
    search_query = f"site:pexels.com/photo {query}"
    encoded_query = search_query.replace(" ", "+").replace('"', '%22')
    
    try:
        result = subprocess.run(
            ["curl", "-sL", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
             f"https://www.google.com/search?q={encoded_query}&num=3"],
            capture_output=True, text=True, timeout=timeout
        )
        
        # Extract Pexels photo URLs with IDs
        # Pattern: /photo/description-12345678/
        pattern = r'pexels\.com/photo/[^/]+-(\d+)/'
        matches = re.findall(pattern, result.stdout)
        
        if matches:
            return matches[0]  # Return first (most relevant) ID
        return None
    except Exception as e:
        return None

def verify_pexels_image(photo_id, timeout=10):
    """Verify that a Pexels photo ID produces a valid image URL."""
    url = f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=400"
    try:
        result = subprocess.run(
            ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=timeout
        )
        return int(result.stdout.strip()) in (200, 301, 302)
    except:
        return False

def build_search_query(product_name, category):
    """Generate an optimal search query for finding a Pexels photo."""
    # Clean product name
    name = product_name.lower()
    
    # Add category context
    cat_context = {
        "Building Materials": "construction building material",
        "Electrical": "electrical wire power",
        "Hardware": "tool workshop hand",
        "IT Equipment": "computer technology office",
        "Machinery": "industrial machine heavy equipment",
        "Food & Beverage": "food product grocery",
        "Chemicals": "chemical liquid industrial",
        "Packaging": "packaging box material",
        "Agriculture": "farming agriculture garden",
        "Furniture": "furniture office home desk",
        "Safety Equipment": "safety protection construction worker",
        "Plumbing": "plumbing pipe water fitting",
        "Textiles": "fabric textile material roll",
        "Automotive": "car automotive vehicle part",
        "Lighting": "light lamp LED bulb",
        "Office Supplies": "office stationery desk paper",
        "Cleaning": "cleaning wash sanitation",
        "Medical Supplies": "medical health hospital equipment",
        "Security": "security surveillance camera protection",
        "Painting": "paint color coating brush",
    }
    
    context = cat_context.get(category, "")
    return f"{name} {context}"

def main():
    print("=" * 70)
    print("  BUILD PEXELS IMAGE MAP")
    print("=" * 70)
    
    # Pre-verified Pexels IDs (from earlier searches)
    known_ids = {
        # Building Materials
        "Portland Cement 50kg": "29817952",
        "Steel Rebar 12mm": "35598611",
        "Ceramic Floor Tiles 60x60": "15273824",
        "Plywood Sheet 12mm": "7479035",
        "Aluminum Window Frame": "9729583",
        "Roofing Sheets": "7930272",
        "Marble Tiles": "3847503",
        # Electrical
        "Solar Panel 300W": "3785079",
        "Copper Cable 2.5mm (100m)": "1615831",
        "Circuit Breaker 32A": "257736",
        "LED Flood Light 100W": "1108572",
        "Diesel Generator 50kVA": "2894946",
        "Transformer 100kVA": "247763",
        "Distribution Panel 12-Way": "257736",
        "UPS 3kVA Online": "3255761",
        "Cable Tray 2m": "1615831",
        "Wall Switch 1-Gang": "1078884",
        "Power Socket Outlet": "1078884",
        "LED Tube Light 1.2m": "1108572",
        "Electrical Conduit Pipe": "1615831",
        "Junction Box IP65": "257736",
        "Extension Cord 50m": "1615831",
        "Surge Protector": "3255761",
        # Hardware
        "Cordless Drill 20V": "4792078",
        "Angle Grinder 115mm": "4792078",
        "Welding Machine MMA 200A": "3825527",
        "Tool Box 3-Tray Metal": "4792078",
        "Adjustable Wrench 12 inch": "4792078",
        "Measuring Tape 5m": "4792078",
        "Hammer Steel 500g": "4792078",
        "Screwdriver Set 12pc": "4792078",
        # IT Equipment
        "Desktop Computer i5": "1714208",
        "Laptop 15.6 inch": "18105",
        "24\" LED Monitor": "1714208",
        "Network Switch 24-Port": "1615831",
        "WiFi Router Dual Band": "3255761",
        "Laser Printer Color": "3760067",
        "UPS 1kVA": "3255761",
        "Server Rack 42U": "3255761",
        "CAT6 Cable 305m": "1615831",
        "Webcam HD 1080p": "4065864",
        "USB Keyboard": "1714208",
        "Wireless Mouse": "1714208",
        # Machinery
        "Excavator 20 Ton": "2894946",
        "Mobile Crane 50 Ton": "2894946",
        "Concrete Mixer 350L": "2894946",
        "Compactor Plate 200kg": "2894946",
        "Air Compressor 100L": "2894946",
        "Water Pump 3HP": "2894946",
        "Industrial Boiler": "2894946",
        "CNC Lathe Machine": "3825527",
        "Hydraulic Press 100T": "3825527",
        "Diesel Generator 100kVA": "2894946",
        "Forklift 3 Ton": "2894946",
        "Welding Inverter 400A": "3825527",
        # Food & Beverage
        "Rice Basmati 25kg": "4750986",
        "Wheat Flour 50kg": "4750986",
        "Cooking Oil 18L": "4750986",
        "Sugar 50kg": "4750986",
        "Canned Tomatoes 400g": "4750986",
        "Milk Powder 25kg": "4750986",
        "Bottled Water 1.5L (24pk)": "1323712",
        "Tea Bags 100pk": "4750986",
        # Safety Equipment
        "Safety Helmet": "6474471",
        "Safety Vest Hi-Vis": "6474471",
        "Work Gloves Leather": "6474471",
        "Safety Goggles": "6474471",
        "Fire Extinguisher 6kg": "6474471",
        "First Aid Kit 50pc": "6474471",
        "Ear Protection Muffs": "6474471",
        "Steel Toe Boots": "6474471",
        # Furniture
        "Office Desk Executive": "1350789",
        "Ergonomic Office Chair": "1350789",
        "Filing Cabinet 4-Drawer": "1350789",
        "Conference Table": "1350789",
        # Cleaning
        "Vacuum Cleaner Industrial": "5591877",
        "Pressure Washer 2000W": "5591877",
        "Broom Set 3pc": "5591877",
        # Lighting
        "LED Bulb 12W": "1108572",
        "Street Light LED 150W": "1108572",
        "Panel Light 60x60": "1108572",
        "Emergency Light Battery": "1108572",
    }
    
    # Search for remaining products
    product_images = {}
    used_ids = set(known_ids.values())
    
    # First, add known IDs
    for name, photo_id in known_ids.items():
        url = f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=400"
        product_images[name] = url
    
    print(f"\nPre-loaded {len(known_ids)} known images")
    
    # Find images for remaining products
    missing = [p for p in PRODUCTS if p["name"] not in product_images]
    print(f"Missing: {len(missing)} products")
    
    for i, p in enumerate(missing):
        name = p["name"]
        cat = p["category"]
        
        query = build_search_query(name, cat)
        photo_id = search_pexels_photo(query)
        
        if photo_id and photo_id not in used_ids:
            # Verify the image exists
            if verify_pexels_image(photo_id):
                url = f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=400"
                product_images[name] = url
                used_ids.add(photo_id)
                print(f"  [{i+1}/{len(missing)}] ✅ {name}: ID {photo_id}")
            else:
                print(f"  [{i+1}/{len(missing)}] ❌ {name}: ID {photo_id} invalid")
        else:
            print(f"  [{i+1}/{len(missing)}] ⚠️  {name}: no unique ID found")
        
        time.sleep(0.5)  # Rate limiting
        
        # Save progress every 20 products
        if (i + 1) % 20 == 0:
            with open("product_images_progress.json", "w") as f:
                json.dump(product_images, f, indent=2)
            print(f"  Progress saved: {len(product_images)}/{len(PRODUCTS)}")
    
    # Final save
    with open("product_images_map.json", "w") as f:
        json.dump(product_images, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"FINAL: {len(product_images)}/{len(PRODUCTS)} products have images")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
