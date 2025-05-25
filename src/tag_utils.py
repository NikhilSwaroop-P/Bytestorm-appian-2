import os
from typing import List, Dict, Any
from blocks.extract_tags import get_tags

def extract_and_add_tags_to_products(products: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
    """
    Extract tags from product descriptions and titles and add them to the product dictionaries.
    
    Args:
        products (List[Dict]): List of product dictionaries
        
    Returns:
        List[Dict]: Products with added tags
    """
    for product in products:
        # Combine title and description for better tag extraction
        text_to_analyze = f"{product.get('title', '')} {product.get('description', '')}"
        
        # Extract tags
        try:
            tags = get_tags(text_to_analyze)
            product['tags'] = tags
        except Exception as e:
            print(f"Error extracting tags: {e}")
            product['tags'] = []
    
    return products

def filter_products_by_tag(products: List[Dict[Any, Any]], tag: str) -> List[Dict[Any, Any]]:
    """
    Filter products by a specific tag.
    
    Args:
        products (List[Dict]): List of product dictionaries with tags
        tag (str): Tag to filter by
        
    Returns:
        List[Dict]: Filtered products that have the specified tag
    """
    tag = tag.lower().strip()
    return [p for p in products if tag in [t.lower() for t in p.get('tags', [])]]

def get_all_tags_from_products(products: List[Dict[Any, Any]]) -> Dict[str, int]:
    """
    Get all unique tags from a list of products with their frequency counts.
    
    Args:
        products (List[Dict]): List of product dictionaries with tags
        
    Returns:
        Dict[str, int]: Dictionary mapping tags to their frequency counts
    """
    tag_counts = {}
    
    for product in products:
        for tag in product.get('tags', []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Sort by frequency
    return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))

if __name__ == "__main__":
    # Example usage
    sample_products = [
        {
            "title": "Prestige Deluxe Plus Pressure Cooker",
            "description": "3L stainless steel pressure cooker with black handle and whistle indicator"
        },
        {
            "title": "Samsung 55-inch QLED Smart TV",
            "description": "4K Ultra HD Smart TV with black bezel and voice control"
        }
    ]
    
    tagged_products = extract_and_add_tags_to_products(sample_products)
    
    print("\nProducts with tags:")
    for product in tagged_products:
        print(f"\n{product['title']}")
        print(f"Tags: {', '.join(product['tags'])}")
    
    print("\nAll tags and counts:")
    all_tags = get_all_tags_from_products(tagged_products)
    for tag, count in all_tags.items():
        print(f"{tag}: {count}") 