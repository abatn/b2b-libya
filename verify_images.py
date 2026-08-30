#!/usr/bin/env python3
"""
Libya B2B — Bilderverifikation
Prüft ALLE 312 Produktbilder auf Gültigkeit und Einzigartigkeit.
Nutzung: python3 verify_images.py
"""

import subprocess
import sys
import os
from collections import Counter

# Ensure we can import backend modules
backend_dir = os.path.join(os.path.dirname(__file__), "src", "backend")
sys.path.insert(0, backend_dir)

from seed_data import PRODUCTS, PRODUCT_IMAGES, SUPPLIER_LOGOS, CATEGORY_IMAGES


def verify_url(url, timeout=10):
    """Prüfe ob eine URL erreichbar ist (HTTP 200/301)."""
    try:
        result = subprocess.run(
            ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=timeout
        )
        status = int(result.stdout.strip())
        return status in (200, 301, 302)
    except (subprocess.TimeoutExpired, ValueError):
        return False


def main():
    print("=" * 70)
    print("  LIBYA B2B — BILDERVERIFIKATION")
    print("=" * 70)

    # ── 1. Produktbilder ──
    print("\n📦 PRODUKTBILDER")
    print("-" * 40)

    valid_products = 0
    invalid_products = 0
    missing_products = 0
    all_urls = []
    duplicate_urls = []

    for p in PRODUCTS:
        name = p["name"]
        url = PRODUCT_IMAGES.get(name)

        if not url:
            missing_products += 1
            print(f"  ❌ MISSING: {name}")
            continue

        if url in all_urls:
            duplicate_urls.append((name, url))
            invalid_products += 1
            print(f"  ❌ DUPLICATE: {name} → {url[:60]}...")
            continue

        all_urls.append(url)

        if verify_url(url):
            valid_products += 1
        else:
            invalid_products += 1
            print(f"  ❌ HTTP ERROR: {name} → {url[:60]}...")

    print(f"\n  ✅ Valid: {valid_products}/{len(PRODUCTS)}")
    print(f"  ❌ Invalid: {invalid_products}")
    print(f"  ❌ Missing: {missing_products}")
    print(f"  ❌ Duplicates: {len(duplicate_urls)}")
    print(f"  📊 Einzigartige Bilder: {len(set(all_urls))}/{len(PRODUCTS)}")

    # ── 2. Supplier-Logos ──
    print("\n🏢 SUPPLIER-LOGOS")
    print("-" * 40)

    valid_logos = 0
    invalid_logos = 0

    for supplier, url in SUPPLIER_LOGOS.items():
        if verify_url(url):
            valid_logos += 1
        else:
            invalid_logos += 1
            print(f"  ❌ HTTP ERROR: {supplier} → {url[:60]}...")

    print(f"\n  ✅ Valid: {valid_logos}/{len(SUPPLIER_LOGOS)}")
    print(f"  ❌ Invalid: {invalid_logos}")

    # ── 3. Kategorie-Bilder ──
    print("\n📂 KATEGORIE-BILDER")
    print("-" * 40)

    valid_cats = 0
    invalid_cats = 0

    for cat, url in CATEGORY_IMAGES.items():
        if verify_url(url):
            valid_cats += 1
        else:
            invalid_cats += 1
            print(f"  ❌ HTTP ERROR: {cat} → {url[:60]}...")

    print(f"\n  ✅ Valid: {valid_cats}/{len(CATEGORY_IMAGES)}")
    print(f"  ❌ Invalid: {invalid_cats}")

    # ── 4. Zusammenfassung ──
    print("\n" + "=" * 70)
    print("  ZUSAMMENFASSUNG")
    print("=" * 70)

    total_images = valid_products + valid_logos + valid_cats
    total_checked = len(PRODUCTS) + len(SUPPLIER_LOGOS) + len(CATEGORY_IMAGES)
    total_invalid = invalid_products + invalid_logos + invalid_cats + missing_products

    print(f"  Bilder gesamt:     {total_checked}")
    print(f"  ✅ Gültig:         {total_images}/{total_checked}")
    print(f"  ❌ Ungültig:       {total_invalid}")
    print(f"  📊 Quote:          {total_images/total_checked*100:.1f}%")

    if total_invalid == 0:
        print("\n  🎉 ALLE BILDER SIND GÜLTIG!")
    else:
        print(f"\n  ⚠️  {total_invalid} Bilder müssen repariert werden")

    # ── 5. Duplikat-Analyse ──
    if duplicate_urls:
        print("\n  🔄 DUPLIKATE (Bild von mehreren Produkten genutzt):")
        for name, url in duplicate_urls:
            print(f"    {name} → {url[:50]}...")

    # ── 6. Fehlende Produkte ──
    products_without_image = [
        p["name"] for p in PRODUCTS if p["name"] not in PRODUCT_IMAGES
    ]
    if products_without_image:
        print(f"\n  📋 PRODUKTE OHNE BILD ({len(products_without_image)}):")
        for name in products_without_image[:20]:
            print(f"    - {name}")
        if len(products_without_image) > 20:
            print(f"    ... und {len(products_without_image) - 20} weitere")

    return total_invalid == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
