#!/usr/bin/env python3
"""
Systematically find real product images for all 312 Libya B2B products.
Uses multiple free sources: Pixabay, Unsplash, Pexels, Wikimedia Commons.
No API keys needed - uses direct URL construction.
"""

import sys
import os
import json
import subprocess
import time
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "backend"))
from seed_data import PRODUCTS

# ============================================================
# SEARCH STRATEGY: For each product, generate multiple search URLs
# ============================================================

def generate_search_urls(product_name, category):
    """Generate search URLs for a product across multiple sources."""
    query = product_name.lower().replace(" ", "+").replace('"', '')
    
    urls = [
        # Pixabay (direct image search)
        f"https://pixabay.com/images/search/{query}/",
        # Pexels
        f"https://www.pexels.com/search/{query}/",
        # Unsplash
        f"https://unsplash.com/s/photos/{query}",
    ]
    return urls

def extract_pexels_ids_from_html(html_content):
    """Extract Pexels photo IDs from HTML content."""
    # Match patterns like /photo/description-12345678/
    pattern = r'/photo/[^/]+-(\d+)/'
    matches = re.findall(pattern, html_content)
    return list(set(matches))

def extract_pixabay_ids_from_html(html_content):
    """Extract Pixabay photo IDs from HTML content."""
    # Match patterns like /photos/photo-name-1234567/
    pattern = r'/photos/[^/]+-(\d+)/'
    matches = re.findall(pattern, html_content)
    return list(set(matches))

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
    print("  PRODUCT IMAGE FINDER")
    print("=" * 70)
    
    # Group products by category
    categories = {}
    for p in PRODUCTS:
        cat = p["category"]
        categories.setdefault(cat, []).append(p["name"])
    
    print(f"\nTotal products: {len(PRODUCTS)}")
    print(f"Categories: {len(categories)}")
    
    # For each category, find relevant Pexels photos
    all_pexels_ids = {}
    
    for cat, products in categories.items():
        print(f"\n--- {cat} ({len(products)} products) ---")
        
        # Search for category-specific Pexels photos
        search_term = cat.lower().replace(" ", "+")
        
        # Use curl to fetch Pexels search page
        try:
            result = subprocess.run(
                ["curl", "-sL", "-A", "Mozilla/5.0", 
                 f"https://www.pexels.com/search/{search_term}/"],
                capture_output=True, text=True, timeout=15
            )
            
            # Extract photo IDs
            photo_ids = extract_pexels_ids_from_html(result.stdout)
            
            if photo_ids:
                print(f"  Found {len(photo_ids)} Pexels photos for '{cat}'")
                # Store unique IDs
                all_pexels_ids[cat] = list(set(photo_ids))[:20]  # Keep top 20
            else:
                print(f"  No photos found for '{cat}' via Pexels")
                
        except Exception as e:
            print(f"  Error searching '{cat}': {e}")
        
        time.sleep(0.5)  # Rate limiting
    
    # Save results
    with open("pexels_ids_by_category.json", "w") as f:
        json.dump(all_pexels_ids, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"RESULTS SAVED TO pexels_ids_by_category.json")
    print(f"{'='*70}")
    
    # Summary
    total_ids = sum(len(ids) for ids in all_pexels_ids.values())
    print(f"\nTotal unique Pexels IDs found: {total_ids}")
    for cat, ids in all_pexels_ids.items():
        print(f"  {cat}: {len(ids)} photos")

if __name__ == "__main__":
    main()
