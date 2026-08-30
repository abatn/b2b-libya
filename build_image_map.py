#!/usr/bin/env python3
"""
Build PRODUCT_IMAGES mapping by searching for each product on Google.
Strategy: Use web_search tool results to find actual product image URLs.
Then verify each URL with curl -I.
"""

import sys
import os
import json
import subprocess
import time
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "backend"))
from seed_data import PRODUCTS

def search_google_images(query, max_results=5):
    """Search Google Images and return image URLs."""
    # Use Google's image search URL
    search_url = f"https://www.google.com/search?q={query}&tbm=isch"
    
    try:
        result = subprocess.run(
            ["curl", "-sL", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
             search_url],
            capture_output=True, text=True, timeout=15
        )
        
        # Extract image URLs from Google Images HTML
        # Google Images embeds image URLs in data attributes
        img_urls = re.findall(r'"(https?://[^"]+\.(?:jpg|jpeg|png|webp))"', result.stdout)
        
        # Filter for actual product images (not Google's UI images)
        product_urls = [u for u in img_urls if 'google' not in u and 'gstatic' not in u]
        
        return product_urls[:max_results]
    except Exception as e:
        return []

def verify_url(url, timeout=10):
    """Verify a URL returns HTTP 200/301/302."""
    try:
        result = subprocess.run(
            ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=timeout
        )
        status = int(result.stdout.strip())
        return status in (200, 301, 302), status
    except:
        return False, 0

def main():
    print("=" * 70)
    print("  BUILD PRODUCT IMAGE MAP")
    print("=" * 70)
    
    # Load existing product images to avoid duplicates
    existing_images = set()
    product_images = {}
    
    # Group products by category
    categories = {}
    for p in PRODUCTS:
        cat = p["category"]
        categories.setdefault(cat, []).append(p["name"])
    
    print(f"\nProducts: {len(PRODUCTS)}")
    print(f"Categories: {len(categories)}")
    
    # Process each category
    for cat, products in categories.items():
        print(f"\n--- {cat} ({len(products)} products) ---")
        
        for product_name in products:
            # Generate search query
            query = f"{product_name} product photo buy"
            
            # Search Google Images
            urls = search_google_images(query, max_results=3)
            
            if urls:
                # Find first unused URL
                for url in urls:
                    if url not in existing_images:
                        # Verify URL
                        ok, status = verify_url(url)
                        if ok:
                            product_images[product_name] = url
                            existing_images.add(url)
                            print(f"  ✅ {product_name}: {url[:60]}... (HTTP {status})")
                            break
                else:
                    print(f"  ⚠️  {product_name}: all URLs already used")
            else:
                print(f"  ❌ {product_name}: no images found")
            
            time.sleep(0.3)  # Rate limiting
    
    # Save results
    with open("product_images_map.json", "w") as f:
        json.dump(product_images, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {len(product_images)}/{len(PRODUCTS)} products mapped")
    print(f"Saved to product_images_map.json")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
