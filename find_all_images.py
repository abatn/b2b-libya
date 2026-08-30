#!/usr/bin/env python3
"""
Systematically find real product images for all 312 Libya B2B products.
Uses Pexels website search to find matching photos for each product.
"""

import sys
import os
import json
import subprocess
import time
import re
import urllib.request
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "backend"))
from seed_data import PRODUCTS


def search_pexels(query, max_results=5):
    """Search Pexels for a product and return photo IDs."""
    encoded = urllib.parse.quote(query)
    url = f"https://www.pexels.com/search/{encoded}/"
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive',
        })
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode('utf-8', errors='ignore')
        
        # Extract photo IDs from search results
        # Pattern: /photo/description-12345678/
        pattern = r'/photo/[^/]+-(\d+)/'
        matches = re.findall(pattern, html)
        
        # Also try to find image URLs directly
        img_pattern = r'images\.pexels\.com/photos/(\d+)'
        img_matches = re.findall(img_pattern, html)
        
        # Combine and deduplicate
        all_ids = list(dict.fromkeys(matches + img_matches))
        return all_ids[:max_results]
    except Exception as e:
        print(f"  ⚠️  Pexels search failed for '{query}': {e}")
        return []


def verify_url(url, timeout=10):
    """Verify a URL returns HTTP 200."""
    try:
        result = subprocess.run(
            ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=timeout
        )
        return int(result.stdout.strip()) in (200, 301, 302)
    except:
        return False


def main():
    print("=" * 70)
    print("  FIND ALL PRODUCT IMAGES - PEXELS SEARCH")
    print("=" * 70)
    
    # Load existing progress if available
    progress_file = "product_images_progress.json"
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            product_images = json.load(f)
        print(f"\nLoaded {len(product_images)} existing images from progress file")
    else:
        product_images = {}
    
    # Track used URLs to avoid duplicates
    used_urls = set(product_images.values())
    
    # Products that need images
    missing = [p for p in PRODUCTS if p["name"] not in product_images]
    print(f"\nProducts needing images: {len(missing)}")
    
    # Process each missing product
    for i, product in enumerate(missing):
        name = product["name"]
        category = product["category"]
        
        # Generate search query - use product name + category context
        query = name.lower()
        # Add category-specific terms for better matching
        category_terms = {
            "Building Materials": "construction building material",
            "Electrical": "electrical equipment power",
            "Hardware": "hand tool power tool hardware",
            "IT Equipment": "computer technology IT",
            "Machinery": "industrial machinery equipment",
            "Food & Beverage": "food product grocery",
            "Chemicals": "chemical product industrial",
            "Packaging": "packaging material supply",
            "Agriculture": "agricultural farming",
            "Furniture": "office furniture",
            "Safety Equipment": "safety protection PPE",
            "Plumbing": "plumbing pipe water",
            "Textiles": "textile fabric material",
            "Automotive": "automotive car part",
            "Lighting": "light LED lighting",
            "Office Supplies": "office stationery supply",
            "Cleaning": "cleaning supply equipment",
            "Medical Supplies": "medical equipment healthcare",
            "Security": "security surveillance safety",
            "Painting": "paint coating wall",
        }
        
        cat_term = category_terms.get(category, "")
        search_query = f"{query} {cat_term} product"
        
        print(f"\n[{i+1}/{len(missing)}] {name} ({category})")
        print(f"  Search: {search_query}")
        
        # Search Pexels
        photo_ids = search_pexels(search_query, max_results=10)
        
        if photo_ids:
            print(f"  Found {len(photo_ids)} Pexels photos")
            
            # Try each photo ID until we find one that works and isn't used
            for pid in photo_ids:
                url = f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=400"
                
                if url in used_urls:
                    continue
                
                if verify_url(url):
                    product_images[name] = url
                    used_urls.add(url)
                    print(f"  ✅ {name}: photo {pid}")
                    break
            else:
                print(f"  ⚠️  All {len(photo_ids)} photos already used or invalid")
        else:
            print(f"  ❌ No photos found")
        
        # Rate limiting
        time.sleep(0.5)
        
        # Save progress every 10 products
        if (i + 1) % 10 == 0:
            with open(progress_file, 'w') as f:
                json.dump(product_images, f, indent=2)
            print(f"\n  💾 Progress saved: {len(product_images)} images")
    
    # Final save
    with open(progress_file, 'w') as f:
        json.dump(product_images, f, indent=2)
    
    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Total products: {len(PRODUCTS)}")
    print(f"  Images found: {len(product_images)}")
    print(f"  Missing: {len(PRODUCTS) - len(product_images)}")
    print(f"  Unique URLs: {len(set(product_images.values()))}")
    
    # Check for duplicates
    urls = list(product_images.values())
    if len(urls) != len(set(urls)):
        print("  ⚠️  WARNING: Duplicate URLs detected!")
    
    print(f"\n  Results saved to: {progress_file}")


if __name__ == "__main__":
    main()
