import google.generativeai as genai
import os
from typing import List

def extract_tags_from_text(text: str, api_key: str =  "AIzaSyAVqQm3ORqqyUsjodZPCVaGFcXCO20OAsI") -> List[str]:
    """
    Extract e-commerce tags/filters from text using Gemini 2.0 Flash.
    
    Args:
        text (str): The input text to extract tags from
        api_key (str, optional): Google API key. If not provided, will try to get from environment variable.
        
    Returns:
        List[str]: A list of extracted tags
    
    Example:
        >>> extract_tags_from_text("Looking for a prestige black stainless steel refrigerator with water dispenser")
        ['prestige', 'black', 'stainless steel', 'refrigerator', 'water dispenser']
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("API key must be provided either as parameter or set as GOOGLE_API_KEY environment variable")
    
    # Configure the Gemini API
    genai.configure(api_key=api_key)
    
    # Initialize the model (using gemini-1.5-flash if 2.0-flash isn't available yet)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Create prompt for tag extraction
    prompt = f"""
    Extract relevant e-commerce product tags/filters from the following text. 
    Return only the tags as a comma-separated list without any explanation or additional text.
    The tags should be features, attributes, brands, colors, materials, etc. that would be useful 
    as filters on an e-commerce site.
    
    Text: {text}
    
    Tags:
    """
    
    # Generate response
    response = model.generate_content(prompt)
    
    # Process response
    tags_text = response.text.strip()
    
    # Split by comma and clean up each tag
    tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
    
    return tags

def get_tags(text: str) -> List[str]:
    """
    Wrapper function to get tags from text.
    Falls back to basic keyword extraction if API is not available.
    
    Args:
        text (str): The input text
        
    Returns:
        List[str]: Extracted tags
    """
    try:
        return extract_tags_from_text(text)
    except Exception as e:
        print(f"Error using Gemini API: {e}")
        # Fallback to basic keyword extraction
        return basic_tag_extraction(text)

def basic_tag_extraction(text: str) -> List[str]:
    """
    Basic tag extraction without using an AI model.
    Used as fallback when API is not available.
    
    Args:
        text (str): Input text
        
    Returns:
        List[str]: Extracted tags
    """
    # Convert to lowercase
    text = text.lower()
    
    # List of common e-commerce tags to check for
    common_tags = [
        # Colors
        "black", "white", "red", "blue", "green", "yellow", "brown", "gray", "silver", "gold",
        # Brands (add relevant brands for your domain)
        "prestige", "samsung", "apple", "sony", "lg", "bosch", "philips", "nike", "adidas",
        # Materials
        "leather", "cotton", "wool", "plastic", "metal", "stainless steel", "glass", "wooden",
        # Features
        "wireless", "waterproof", "smart", "automatic", "manual", "portable", "rechargeable",
        # Product types
        "shirt", "pants", "dress", "shoes", "refrigerator", "tv", "laptop", "phone", "camera"
    ]
    
    # Find matches
    found_tags = []
    for tag in common_tags:
        if tag in text or tag.replace(" ", "") in text:
            found_tags.append(tag)
    
    return found_tags

if __name__ == "__main__":
    # Example usage
    sample_text = "I'm looking for a prestige pressure cooker in black color with timer function"
    print(f"Input: {sample_text}")
    
    try:
        tags = get_tags(sample_text)
        print(f"Extracted tags: {tags}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to set your GOOGLE_API_KEY environment variable!") 