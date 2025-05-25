import os
from mistralai import Mistral
import time
import json
# Initialize client
api_key = 'VrAMhIHO61FjHTAYeibtLmla52bWnorV'
model = 'mistral-large-latest'
client = Mistral(api_key=api_key)

prompt_template_splitter = '''
You are given a product-related query from a user. Your task is to split the query into two meaningful parts:

1. "general" — Describes general product characteristics like type, color, material, brand, features (e.g., "red t-shirt", "leather wallet", "brand XYZ", "Bluetooth headset", "made of cotton", "for kids", etc.)
2. "special" — Describes specific requirements or filters like price range, exact price, user ratings, rating count, discount, availability, etc. (e.g., "price between 100-200", "at least 4.5 stars", "over 1000 ratings", "under $20", etc.)
Rule: You should not change the query or any part of it. Just split it into two parts as described above.
Each part should be self-contained and make sense on its own. If one category has no relevant details, it should be returned as an empty string.

### Output Format:
```json
{{
  "general": "text describing general product characteristics",
  "special": "text describing specific filters or constraints"
}}
```

### Few-Shot Examples:

**Example 1:**
Query: *"Blue denim jeans under 50 dollars with at least 500 reviews and a rating above 4.2 from brand Levis"*

```json
{{
  "general": "Blue denim jeans from brand Levis",
  "special": "under 50 dollars with at least 500 reviews and a rating above 4.2"
}}
```

**Example 2:**
Query: *"Black wireless headphones with noise cancellation and a price range of 100 to 200 dollars, rating of 4.7 stars"*

```json
{{
  "general": "Black wireless headphones with noise cancellation",
  "special": "price range of 100 to 200 dollars, rating of 4.7 stars"
}}
```

**Example 3:**
Query: *"Red cotton t-shirt with a price range of 10-20 dollars and a rating of 4.5 with at least 1000 ratings. The t-shirt should have long sleeves and be of brand XYZ. The t-shirt should be available in size M and L."*

```json
{{
  "general": "Red cotton t-shirt with long sleeves from brand XYZ, available in size M and L",
  "special": "price range of 10-20 dollars and a rating of 4.5 with at least 1000 ratings"
}}
```

**Example 4 (empty special):**
Query: *"Leather wallet from Fossil"*

```json
{{
  "general": "Leather wallet from Fossil",
  "special": ""
}}
```

**Example 5 (empty general):**
Query: *"Under $20 and with at least 100 reviews"*

```json
{{
  "general": "",
  "special": "under $20 and with at least 100 reviews"
}}
```

### Now split this query:
"""
{query_text}
"""
'''

conflict_prompt_template = '''
You are given two texts:
1. Current text describing the product's existing features.
2. Modification text describing what the customer now wants.

Determine if the customer's new request conflicts with existing features. Conflict arises if they request something that contradicts current settings (e.g., color, size, feature availability).

Return True if there is a conflict, otherwise return False.

### Output Format:
```
True
``` or ```
False
```

### Few-Shot Examples:

**Example 1 (No Conflict):**
Current: "Red cotton t-shirt sizes S, M, L"
Customer: "Long sleeves"
Output: False

**Example 2 (Conflict):**
Current: "Red cotton t-shirt sizes S, M, L"
Customer: "Blue color"
Output: True

**Example 3 (No Conflict):**
Current: "Laptop with touchscreen and backlit keyboard"
Customer: "RFID protection"
Output: False

**Example 4 (Conflict):**
Current: "Laptop with touchscreen and backlit keyboard"
Customer: "No touchscreen"
Output: True

**Example 5 (Conflict):**
Current: "Shoes sizes 8, 9, 10"
Customer: "Only size 7"
Output: True

Now evaluate:
Current:
"""
{current_text}
"""
Customer:
"""
{modification_text}
"""
'''

update_prompt_template = '''
You are given two texts:
1. Current text describing the product's existing features.
2. Modification text describing what the customer now wants.

Your task is to merge the customer's new requests into the current product description following these rules:
- **Add a feature**: If the customer requests a new feature, append it.
- **Explicit removal**: If the customer specifies "no X", retain other features and include "no X".
- **Optional removal**: If the customer expresses that a feature is optional or not needed, remove that feature entirely.
- **Override a feature**: If the customer specifies a change (e.g., new color), replace the old feature.
Rule: if the current text has a feature that is conflicting with the modification text repeated, even then modify all that to modification text's features.
Return the updated product description as a concise, coherent text.

### Output Format:
Output:```result...
```

### Few-Shot Examples:

**Example 1 (Override color):**
Current: "Red cotton t-shirt sizes S, M, L, long sleeves"
Customer: "Blue color"
Output: "Blue cotton t-shirt sizes S, M, L, long sleeves"

**Example 2 (Add feature):**
Current: "Leather wallet from Fossil, no RFID protection"
Customer: "RFID protection"
Output: "Leather wallet from Fossil, RFID protection"

**Example 3 (Restrict size):**
Current: "Shoes sizes 8, 9, 10"
Customer: "Only size 7"
Output: "Shoes size 7"

**Example 4 (Explicit removal):**
Current: "Laptop with touchscreen and backlit keyboard"
Customer: "No touchscreen"
Output: "Laptop with no touchscreen and backlit keyboard"

**Example 5 (Optional removal):**
Current: "Laptop with touchscreen and backlit keyboard"
Customer: "Touchscreen optional"
Output: "Laptop with backlit keyboard"

**Example 6 (Feature conflict override - moderate):**
Current: "Smartphone with dual rear cameras, silver body, dual rear cameras, and 6GB RAM"
Customer: "Gold body, 8GB RAM"
Output: "Smartphone with dual rear cameras, gold body, and 8GB RAM"

**Example 7 (Feature conflict override - difficult):**
Current: "NoiseFit Buzz smartwatch with black strap, round dial, black strap, and voice calling feature, black strap"
Customer: "Blue strap, square dial"
Output: "NoiseFit Buzz smartwatch with blue strap, square dial, and voice calling feature"

**Example 8 (Brand and feature override with repetition):**
Current: "The Prestige dry iron features a lightweight design, adjustable temperature settings, and non-stick soleplate for smooth ironing performance, with its white and turquoise exterior. - Prestige White, Turquoise Appliance, Prestige dry iron."
Customer: "Philips brand, black and silver color"
Output: "Philips dry iron with a lightweight design, adjustable temperature settings, non-stick soleplate for smooth ironing performance, and black and silver exterior"

Now merge:
Current:
"""
{current_text}
"""
Customer:
"""
{modification_text}
"""
'''



def split_query(query: str) -> str:
    content = prompt_template_splitter.format(query_text=query)
    response = client.chat.complete(
        model=model,
        messages=[{'role': 'user', 'content': content}]
    )
    output = response.choices[0].message.content
    # extracting the json part
    start = output.find('{')
    end = output.rfind('}') + 1
    json_part = output[start:end]
    # convert json part to dictionary
    try:
        json_data = json.loads(json_part)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        json_data = {}
    out_dict = dict(json_data)
    if 'general' not in out_dict or 'special' not in out_dict:
        print(f"Error: Missing keys in output: {out_dict}")
    return out_dict

def conflict_check(current_text: str, modification_text: str) -> bool:
    """Return True if the modification_text conflicts with current_text."""
    content = conflict_prompt_template.format(
        current_text=current_text,
        modification_text=modification_text
    )
    response = client.chat.complete(
        model=model,
        messages=[{'role': 'user', 'content': content}]
    )
    answer = response.choices[0].message.content.strip()
    # print(answer)
    k = answer.lower().split('```')
    if 'true' in k:
        return True
    else:
        return False

def update_current_text(current_text: str, modification_text: str) -> str:
    """Merge modification_text into current_text."""
    content = update_prompt_template.format(
        current_text=current_text,
        modification_text=modification_text
    )
    response = client.chat.complete(
        model=model,
        messages=[{'role': 'user', 'content': content}]
    )
    out = response.choices[0].message.content.strip().split('```')
    return out[1]