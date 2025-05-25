from email.mime import image
from blocks.product_description_generator import ProductDescriptionGenerator
import json
generator = ProductDescriptionGenerator()

def discription(image_path: str = None):
    """
    Generate backbone and detailed product descriptions from an image.
    
    Args:
        image_path (str): Path to the product image
        
    Returns:
        tuple: (backbone_description, detailed_description, raw_detailed_data) as strings and dict
    """
    global generator
    try:
        # Generate descriptions
        result = generator.generate_product_descriptions(image_path)
        
        if "error" in result:
            return "Error generating description", f"Error: {result['error']}"
            
        # Create backbone description string
        backbone = result['backbone_description']
        backbone_str = f"{backbone['title']} - {backbone['description']} - {backbone['category']}"
        
        # Create detailed description string
        detailed = result['detailed_description']
        detailed_str = f"{detailed['title']} - {detailed['description']} - {detailed['brand']} {detailed['color']} {detailed['category']}"
        
        # Return both strings and the raw detailed data
        return backbone_str, detailed_str
        
    except Exception as e:
        return f"Error: {str(e)}", f"Error: {str(e)}"


def text_split(query: str): #default description
    a = generator.split_text_query(query)
    raw = a.text.split("```")[1]
    if raw.lstrip().startswith("json"):
        raw = raw.lstrip()[4:].lstrip("\n")
    data = json.loads(raw)
    return data['backbone'], data['detailed_description']

def modify_query(image_path: str = None, query: str = None) -> str:

#    if image_path:
#         query = generator.modify_query(image_path, query).text
   return query

def modify_query_text(backbone, original_current_text) -> str:

    """
    Modify the query based on the provided image.
    """
    # Example modification logic
    modified_query = "Modified query based on image"
    return modified_query

def intention(image_path: str = None, query: str = None) -> str:
    if query is None:
        query = ""
    return generator.intention_check(image_path, query)

def alternate_current_text(current_text, modification_text) -> str:
    
    
    return generator.update_current_text(current_text, modification_text)
