import os
import json
import google.generativeai as genai
from PIL import Image

class ProductDescriptionGenerator:
    def __init__(self, api_key='AIzaSyBS2npulOMMZ9WRj7b-UpoYHXVSa0Jju4o'):
        """
        Initialize the ProductDescriptionGenerator with Google Gemini.
        
        Args:
            api_key (str, optional): Google API key for Gemini. If None, looks for GOOGLE_API_KEY env variable.
        """
        if api_key is None:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if api_key is None:
                raise ValueError("No API key provided. Set GOOGLE_API_KEY environment variable or pass as parameter.")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def _prepare_image(self, image_path):
        """Helper method to load and prepare an image for the API."""
        if isinstance(image_path, str):
            # If path is provided as string
            img = Image.open(image_path)
        else:
            # If PIL Image is directly provided
            img = image_path
            
        # Resize if the image is too large
        max_size = 4000  # Gemini has size limits
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size))
            
        return img
    
    def _extract_section(self, text, section_name, next_sections=None):
        """
        Extract a specific section from the response text.
        
        Args:
            text: Full response text
            section_name: Name of the section to extract
            next_sections: List of section names that might follow this one
            
        Returns:
            str: Extracted section content or empty string if not found
        """
        parts = text.split(f"{section_name}:", 1)
        if len(parts) < 2:
            return ""
        
        content = parts[1].strip()
        
        # Find where the next section begins
        if next_sections:
            min_pos = len(content)
            for section in next_sections:
                section_marker = f"\n{section}:"
                pos = content.find(section_marker)
                if pos != -1 and pos < min_pos:
                    min_pos = pos
            
            if min_pos < len(content):
                content = content[:min_pos].strip()
        
        return content
    
    def generate_product_descriptions(self, image_path):
        """
        Generate both backbone and detailed product descriptions from an image.
        Optimized for retrieval with minimal, non-repetitive content.
        
        Args:
            image_path: Path to the image file or PIL Image object
            
        Returns:
            dict: Contains both backbone and detailed descriptions
        """
        try:
            img = self._prepare_image(image_path)
            
            # Make a single comprehensive prompt to extract all needed information
            comprehensive_prompt = """
            Analyze this image and provide EXTREMELY BRIEF product descriptions in this EXACT format:

            BRIEF_TITLE: [Product title with brand, max 6 words]
            DETAIL_DESC: [Complete description with brand and color, exactly 10-20 words]
            GENERIC_TITLE: [Generic title without brand, max 5 words]
            GENERIC_DESC: [Generic description without brand/color mentions, exactly 5-15 words]
            CATEGORY: [Product category, 1-2 words only]
            BRAND: [Brand name only, single word if possible]
            COLOR: [Main color(s), 1-2 words maximum]
            KEY_SPECS: [3-4 key specifications, comma-separated, no brand/color mentions]

            Follow these rules strictly:
            1. Be extremely concise - do not exceed word limits
            2. For GENERIC fields, absolutely no brand or color mentions
            3. Keep each response as short as possible while remaining descriptive
            4. Each section must be on its own line
            5. Do not repeat information between sections
            """
            
            response = self.model.generate_content([comprehensive_prompt, img])
            response_text = response.text.strip()
            
            # Define all section names to help with extraction
            sections = [
                "BRIEF_TITLE", "DETAIL_DESC", "GENERIC_TITLE", "GENERIC_DESC",
                "CATEGORY", "BRAND", "COLOR", "KEY_SPECS"
            ]
            
            # Extract each section
            detailed = {}
            
            # Extract each section, knowing what section might follow it
            for i, section in enumerate(sections):
                next_section_list = sections[i+1:] if i < len(sections) - 1 else None
                content = self._extract_section(response_text, section, next_section_list)
                
                # Map section names to our field names
                if section == "BRIEF_TITLE":
                    detailed["title"] = content
                elif section == "DETAIL_DESC":
                    detailed["description"] = content
                elif section == "GENERIC_TITLE":
                    detailed["generic_title"] = content
                elif section == "GENERIC_DESC":
                    detailed["generic_description"] = content
                elif section == "CATEGORY":
                    detailed["category"] = content
                elif section == "BRAND":
                    detailed["brand"] = content
                elif section == "COLOR":
                    detailed["color"] = content
                elif section == "KEY_SPECS":
                    # Further filter specs to ensure no brand/color mentions
                    specs = [spec.strip() for spec in content.split(",")]
                    detailed["key_specs"] = specs
            
            # Create backbone description (without brand or color)
            backbone = {
                "title": detailed.get("generic_title", ""),
                "description": detailed.get("generic_description", ""),
                "category": detailed.get("category", ""),
                "key_specs": self._filter_brand_color_mentions(
                    detailed.get("key_specs", []),
                    detailed.get("brand", ""),
                    detailed.get("color", "")
                )
            }
            
            # Create result with both descriptions
            result = {
                "backbone_description": backbone,
                "detailed_description": {
                    "title": detailed.get("title", ""),
                    "description": detailed.get("description", ""),
                    "brand": detailed.get("brand", ""),
                    "color": detailed.get("color", ""),
                    "category": detailed.get("category", ""),
                    "key_specs": detailed.get("key_specs", [])
                }
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def _filter_brand_color_mentions(self, specs, brand, color):
        """Filter out any specs containing brand or color mentions"""
        filtered = []
        
        if not brand and not color:
            return specs
            
        brand_terms = [b.lower() for b in brand.split()] if brand else []
        color_terms = [c.lower() for c in color.split()] if color else []
        
        for spec in specs:
            spec_lower = spec.lower()
            contains_brand_or_color = False
            
            # Check for brand terms
            for term in brand_terms:
                if term and len(term) > 1 and term in spec_lower:
                    contains_brand_or_color = True
                    break
                    
            # Check for color terms
            if not contains_brand_or_color:
                for term in color_terms:
                    if term and len(term) > 1 and term in spec_lower:
                        contains_brand_or_color = True
                        break
            
            if not contains_brand_or_color:
                filtered.append(spec)
                
        return filtered
    
    def save_product_descriptions(self, image_path, output_dir=None, prefix=None):
        """
        Generate product descriptions and save both backbone and detailed descriptions as JSON files.
        
        Args:
            image_path: Path to the image file or PIL Image object
            output_dir: Directory to save JSON files. If None, uses image directory
            prefix: Prefix for output filenames. If None, uses image filename
            
        Returns:
            dict: Paths to saved JSON files
        """
        try:
            # Generate the product descriptions
            descriptions = self.generate_product_descriptions(image_path)
            
            if "error" in descriptions:
                return {"error": descriptions["error"]}
            
            # Determine output directory and prefix
            if isinstance(image_path, str):
                if output_dir is None:
                    output_dir = os.path.dirname(image_path)
                if prefix is None:
                    prefix = os.path.splitext(os.path.basename(image_path))[0]
            else:
                if output_dir is None or prefix is None:
                    raise ValueError("output_dir and prefix must be provided when image_path is not a string")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Save backbone description
            backbone_path = os.path.join(output_dir, f"{prefix}_backbone.json")
            with open(backbone_path, 'w', encoding='utf-8') as f:
                json.dump(descriptions["backbone_description"], f, indent=2, ensure_ascii=False)
            
            # Save detailed description
            detailed_path = os.path.join(output_dir, f"{prefix}_detailed.json")
            with open(detailed_path, 'w', encoding='utf-8') as f:
                json.dump(descriptions["detailed_description"], f, indent=2, ensure_ascii=False)
            
            # Save combined descriptions
            combined_path = os.path.join(output_dir, f"{prefix}_combined.json")
            with open(combined_path, 'w', encoding='utf-8') as f:
                json.dump(descriptions, f, indent=2, ensure_ascii=False)
            
            return {
                "backbone_path": backbone_path,
                "detailed_path": detailed_path,
                "combined_path": combined_path
            }
            
        except Exception as e:
            return {"error": str(e)}

    def modify_query(self, image_path: str, modification_text: str) -> str:
            """
            Rewrite `modification_text` by replacing any “same color”, “same brand”, “same model”,
            “same functions”, “same specifications” or “same features” with the actual attributes
            extracted from the image. If the user explicitly asks for a conflicting color, brand/model,
            functions, specs, or features, those parts are left untouched.
            Think carefully about how to rewrite the text so that it
            accurately reflects the image attributes while respecting user modifications.
            """
            rewrite_prompt = f"""
    You are a rewriting assistant that:
    1. Examines the image and pulls out its actual color, brand/model, functions,
        specifications (e.g. size, memory, power), and key features (e.g. waterproof,
        energy-saving).
    2. Substitutes any phrase like "same color", "same brand", "same model",
        "same functions", "same specifications", or "same features" in the user’s
        modification text with those real values.
    3. Leaves untouched any part where the user explicitly specifies a different
        value (e.g., "white color" when the image is black).

    Examples:

    1) Image: [a red Nike Air Max sneaker, functions: running support; specifications: size 10; features: air cushion]
    Mod: "nike shoes in the same color, model, and functions as the image."
    Rewrite: "nike shoes in red color, Air Max model, and running support functions."

    2) Image: [a black Philips iron, functions: steam ironing; specifications: 1200W; features: auto‐shutoff]
    Mod: "same brand as image and white color, with same specifications."
    Rewrite: "Philips iron in white color, with 1200W specifications."

    3) Image: [a blue Sony WH-1000XM4 headphones, functions: noise cancellation; specifications: 30-hour battery; features: touch controls]
    Mod: "show me white Sony headphones with the same features."
    Rewrite: "show me white Sony headphones with touch controls features."

    4) Image: [a green Samsung Galaxy S21, functions: calling/texting/internet; specifications: 6.2in screen, 8GB RAM, 128GB storage; features: 5G, waterproof]
    Mod: "same brand and model but in black, and add same specifications."
    Rewrite: "Samsung Galaxy S21 in black, and add 6.2-inch screen, 8GB RAM, 128GB storage specifications."

    Now rewrite this modification text using the image below:

    Modification text: "{modification_text}"
    """
            # Pass the prompt and the prepared image to Gemini Flash 2 in one go:
            return self.model.generate_content([
                rewrite_prompt,
                self._prepare_image(image_path)
            ])

    def split_text_query(self, query: str) -> str:
        """
        Splits a free-form product query into:
          • backbone: the generic product type(s) only (one or multiple products, e.g., "hiking boots" or "lamp, sofa, AC"),
            with NO brand, color, model, specs, or features.
          • detailed_description: the original full query including all specifics.

        Returns a JSON string:
        {
          "backbone": "...",
          "detailed_description": "..."
        }
        """
        prompt = f"""
You are an assistant that reads a product query and returns a JSON object with two keys:
  • backbone: the generic product type(s) only (can be one or more items, comma-separated or 'and'-joined),
    e.g., "lamp, sofa, AC", with NO brand, color, model, specs, or features.
  • detailed_description: the original full query including all specifics.

Examples:

Query: "Nike shoes in red color and Air Max model"
Output:
{{
  "backbone": "shoes",
  "detailed_description": "Nike shoes in red color and Air Max model"
}}

Query: "Black Philips iron with 1200W steam function and auto-shutoff feature"
Output:
{{
  "backbone": "iron",
  "detailed_description": "Black Philips iron with 1200W steam function and auto-shutoff feature"
}}

Query: "Wireless noise-cancelling Sony WH-1000XM4 headphones in white"
Output:
{{
  "backbone": "wireless noise-cancelling headphones",
  "detailed_description": "Wireless noise-cancelling Sony WH-1000XM4 headphones in white"
}}

Query: "Waterproof hiking boots with ankle support and Vibram soles"
Output:
{{
  "backbone": "waterproof hiking boots",
  "detailed_description": "Waterproof hiking boots with ankle support and Vibram soles"
}}

Query: "Modern living room set: lamp, sofa, and AC with remote control, LED lighting, and energy-saving mode"
Output:
{{
  "backbone": "lamp, sofa, AC",
  "detailed_description": "Modern living room set: lamp, sofa, and AC with remote control, LED lighting, and energy-saving mode"
}}

Now process this query:

Query: "{query}"
"""
        return self.model.generate_content([prompt])
    
    def intention_check(self, image_path: str, user_query: str = None) -> dict:
        """
        Classifies a user’s intention based on an uploaded image and optional text query into one of two intents,
        and when intent is "space_improvement_or_replacement", also provides a
        single query string with multiple product recommendations.

        Returns a dict:
        {
          "intent": "similar_product" | "space_improvement_or_replacement",
          "recommendations_query": "..."  # present only if intent is class 2
        }
        """
        # Base intent instruction
        intent_prompt = f"""
You are an intent-classifier and recommender. Given the image{(' and the user query: ' + user_query) if user_query else ''}, decide the user's intent:
  1) "similar_product": they want products visually similar to the image.
  2) "space_improvement_or_replacement": they want recommendations for room/space improvements or replacement parts.
the intent is space_improvement_or_replacement if the image shows multiple products or, only a part of a product is damaged. if the image shows a single product even if it is damaged, the intent is similar_product.
If intent is "space_improvement_or_replacement", also generate a single query string listing several products they might consider, e.g., "modern floor lamp, LED ceiling light, minimalist bookshelf".
stick to the following format:
```json
{{
  "intent": "similar_product" | "space_improvement_or_replacement",
  "recommendations_query": "..."  # present only if intent is class 2
}}```
Examples:

1) Image: [sneaker photo]
   Output:
   ```json{{
     "intent": "similar_product"
   }}```

2) Image: [broken iron handle]
   Output:
   ```json
   {{
     "intent": "space_improvement_or_replacement",
     "recommendations_query": "replacement iron handle, universal steam iron knob, high-heat resistant knob"
   }}\n```

3) Image: [living room photograph]
   Output:
   ```json
   {{
     "intent": "space_improvement_or_replacement",
     "recommendations_query": "modern floor lamp, LED ceiling light, minimalist bookshelf, pots,..."
   }}\n```

4) Image: [photo of an appliance]
   Output:
   ```json
   {{
     "intent": "similar_product"
   }}```

Now analyze and respond with JSON:
"""
        # Prepare inputs
        inputs = [intent_prompt, self._prepare_image(image_path)]
        # If there is a user text query, append it to the context
        if user_query:
            inputs.append(user_query)
        raw = self.model.generate_content(inputs)
        print(raw.text)

        raw = raw.text.split("```")[1]
        if raw.lstrip().startswith("json"):
            raw = raw.lstrip()[4:].lstrip("\n")
        data = json.loads(raw)
        if data.get("intent") == "space_improvement_or_replacement":
            data['intent'] = 1
        elif data.get("intent") == "similar_product":
            data['intent'] = 0
        else:
            raise ValueError("Invalid intent returned from Gemini. Expected 'similar_product' or 'space_improvement_or_replacement'.")
        return data

    def update_current_text(self, current_text: str, modification_text: str) -> str:
        """
        Merge the customer's modification text into the current product description,
        validate, and return the confirmed update. Always output and parse JSON.
        Uses only the Gemini model.
        """
        # Build few-shot examples
        examples = [
            ("Red cotton t-shirt sizes S, M, L, long sleeves", "Blue color", "Blue cotton t-shirt sizes S, M, L, long sleeves"),
            ("Leather wallet from Fossil, no RFID protection", "RFID protection", "Leather wallet from Fossil, RFID protection"),
            ("Shoes sizes 8, 9, 10", "Only size 7", "Shoes size 7"),
            ("Laptop with touchscreen and backlit keyboard", "No touchscreen", "Laptop with no touchscreen and backlit keyboard"),
            ("Laptop with touchscreen and backlit keyboard", "Touchscreen optional", "Laptop with backlit keyboard"),
            ("Smartphone with dual rear cameras, silver body, dual rear cameras, and 6GB RAM", "Gold body, 8GB RAM", "Smartphone with dual rear cameras, gold body, and 8GB RAM"),
            ("NoiseFit Buzz smartwatch with black strap, round dial, black strap, and voice calling feature, black strap", "Blue strap, square dial", "NoiseFit Buzz smartwatch with blue strap, square dial, and voice calling feature"),
            ("The Prestige dry iron features a lightweight design, adjustable temperature settings, and non-stick soleplate for smooth ironing performance, with its white and turquoise exterior.",
             "Philips brand, black and silver color",
             "Philips dry iron with a lightweight design, adjustable temperature settings, non-stick soleplate for smooth ironing performance, and black and silver exterior")
        ]
        # Assemble few-shot text
        shot_section = "\n".join(
            f"Current: '{c}'\nCustomer: '{m}'\nExpected: '{{\"updated_text\": \"{o}\"}}'"
            for c, m, o in examples
        )
        # Prompt user
        prompt = f"""
You are an assistant that merges two texts following rules:
- Add new features by appending.
- If customer says 'no X', include 'no X'.
- If a feature is optional, remove it.
- Override conflicting features with new values.

Provide output strictly as JSON: {{"updated_text": "..."}}

Examples:
{shot_section}

Now merge:
Current: '{current_text}'
Customer: '{modification_text}'

Respond with JSON only.
"""
        # Generate and parse
        raw = self.model.generate_content([prompt]).text
        # Extract JSON substring
        start = raw.find('{')
        end = raw.rfind('}') + 1
        json_str = raw[start:end] if start != -1 and end != -1 else raw
        try:
            data = json.loads(json_str)
            return data.get('updated_text', json_str)
        except json.JSONDecodeError:
            return json_str

        
# Example usage
if __name__ == "__main__":
    generator = ProductDescriptionGenerator()
    
    # Test with a sample image
    image_path = r"datasets\amazon-2023-filtered100\images\Bajaj_mixer_Grinder_Chutney_jar_0.4_L_(Steel_Black_28.jpg"  # Change to your test image path
    
    try:
        # Generate both backbone and detailed descriptions
        result = generator.generate_product_descriptions(image_path)
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            # Print both descriptions
            print("=" * 80)
            print("BACKBONE DESCRIPTION (WITHOUT COLOR/BRAND)")
            print("=" * 80)
            print(f"Title: {result['backbone_description']['title']}")
            print(f"Description: {result['backbone_description']['description']}")
            print(f"Category: {result['backbone_description']['category']}")
            print("Key Specs:")
            for spec in result['backbone_description']['key_specs']:
                print(f"- {spec}")
            
            print("\n" + "=" * 80)
            print("DETAILED DESCRIPTION (WITH COLOR/BRAND)")
            print("=" * 80)
            print(f"Title: {result['detailed_description']['title']}")
            print(f"Description: {result['detailed_description']['description']}")
            print(f"Brand: {result['detailed_description'].get('brand', 'N/A')}")
            print(f"Color: {result['detailed_description'].get('color', 'N/A')}")
            print(f"Category: {result['detailed_description'].get('category', 'N/A')}")
            print("Key Specs:")
            for spec in result['detailed_description'].get('key_specs', []):
                print(f"- {spec}")
            
    except Exception as e:
        print(f"Error: {e}") 