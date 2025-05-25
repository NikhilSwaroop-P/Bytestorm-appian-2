#!/usr/bin/env python3
"""
Test script to demonstrate the tag extraction functionality.
"""

import os
import sys
import argparse
from blocks.extract_tags import get_tags, extract_tags_from_text
from tag_utils import extract_and_add_tags_to_products, filter_products_by_tag, get_all_tags_from_products

def main():
    parser = argparse.ArgumentParser(description="Test tag extraction from text using Gemini 2.0 Flash")
    parser.add_argument("--text", type=str, help="Text to extract tags from")
    parser.add_argument("--api-key", type=str, help="Google API key (can also be set as GOOGLE_API_KEY env var)")
    parser.add_argument("--file", type=str, help="File with example product data (JSON format)")
    
    args = parser.parse_args()
    
    # Set API key if provided
    if args.api_key:
        os.environ["GOOGLE_API_KEY"] = args.api_key
    
    # Process text if provided
    if args.text:
        print(f"\nInput text: {args.text}")
        try:
            tags = get_tags(args.text)
            print(f"Extracted tags: {tags}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    # Process file if provided
    if args.file:
        try:
            import json
            with open(args.file, 'r') as f:
                products = json.load(f)
            
            print(f"\nLoaded {len(products)} products from {args.file}")
            tagged_products = extract_and_add_tags_to_products(products)
            
            # Display some sample results
            for i, product in enumerate(tagged_products[:3]):  # Show first 3 for brevity
                print(f"\nProduct {i+1}: {product.get('title', 'Untitled')}")
                print(f"Tags: {', '.join(product.get('tags', []))}")
            
            # Show tag stats
            tag_counts = get_all_tags_from_products(tagged_products)
            print("\nTop 10 tags:")
            for i, (tag, count) in enumerate(list(tag_counts.items())[:10]):
                print(f"{tag}: {count} products")
                
        except Exception as e:
            print(f"Error processing file: {e}")
            return 1
    
    # If no arguments provided, show usage examples
    if not args.text and not args.file:
        print_usage_examples()
    
    return 0

def print_usage_examples():
    print("\nTag Extraction Demo")
    print("==================")
    print("\nUsage examples:")
    print("  Extract tags from text:")
    print("    python test_tag_extraction.py --text \"I'm looking for a black Samsung TV with 4K resolution\"")
    print("\n  Extract tags using specific API key:")
    print("    python test_tag_extraction.py --api-key YOUR_API_KEY --text \"Prestige pressure cooker with timer\"")
    print("\n  Process products from a JSON file:")
    print("    python test_tag_extraction.py --file sample_products.json")
    
    # Generate a simple example product JSON
    print("\nExample JSON file format:")
    example = [
        {
            "title": "Prestige Deluxe Plus Pressure Cooker",
            "description": "3L stainless steel pressure cooker with black handle and whistle indicator"
        },
        {
            "title": "Samsung 55-inch QLED Smart TV",
            "description": "4K Ultra HD Smart TV with black bezel and voice control"
        }
    ]
    import json
    print(json.dumps(example, indent=2))

if __name__ == "__main__":
    sys.exit(main()) 