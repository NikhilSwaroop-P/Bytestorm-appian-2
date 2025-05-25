import json
import re
import time
from mistralai import Mistral

api_key = 'VrAMhIHO61FjHTAYeibtLmla52bWnorV'
model = 'mistral-small-latest'
client = Mistral(api_key=api_key)

# Prompt template with multiple few-shot examples
# Note: Use doubled braces to escape literal JSON braces in .format
special_case_prompt_template = '''
Given an input text, split it into three filters with their corresponding numeric ranges or counts.
The filters are: price, rating, and rating count.

Examples:
1. Input: "with price range of 100 to 200 dollars, rating of 4.7 stars"
   Output:
   ```json
   {{"price": [100, 200], "rating": [4.7, 5], "rating_count": null}}
   ```

2. Input: "rating of at least 3.5"
   Output:
   ```json
   {{"price": null, "rating": [3.5, 5], "rating_count": null}}
   ```

3. Input: "rating count between 50 and 200 reviews, price up to 150 dollars"
   Output:
   ```json
   {{"price": [0, 150], "rating": null, "rating_count": [50, 200]}}
   ```

4. Input: "price between 10 and 50, rating of 4 stars, rating count at least 100"
   Output:
   ```json
   {{"price": [10, 50], "rating": [4, 5], "rating_count": [100, null]}}
   ```

5. Input: "" (empty)
   Output:
   ```json
   {{"price": null, "rating": null, "rating_count": null}}
   ```

Now, process the following input:
"{query_text}"
Return only the JSON object.
'''

def special_case_split(query_dict, client, model) -> dict:
    """
    Extracts price, rating, and rating_count filters from the 'special' field of query_dict.
    Returns a dict with keys 'price', 'rating', 'rating_count', each mapping to [min, max] or None.
    For empty input, returns all keys with None.
    """
    special_case_text = query_dict.get('special', '')
    # Default output for empty or missing special text
    if not special_case_text:
        return { 'price': None, 'rating': None, 'rating_count': None }

    # Prepare the LLM prompt
    content = special_case_prompt_template.format(query_text=special_case_text)

    try:
        # Call the chat API
        response = client.chat.complete(
            model=model,
            messages=[{'role': 'user', 'content': content}]
        )
        output = response.choices[0].message.content.strip()

        # Extract JSON substring
        match = re.search(r"\{[\s\S]*\}", output)
        json_part = match.group(0) if match else ''

        # Parse JSON to dict, converting null to None
        json_data = json.loads(json_part) if json_part else {}
        # Ensure Python None for null (explicit)
        for key in ['price', 'rating', 'rating_count']:
            if key not in json_data or json_data.get(key) is None or json_data.get(key) == 'null':
                json_data[key] = None
        return dict(json_data)

    except Exception as e:
        print(f"Error during parsing special case: {e}")
        return { 'price': None, 'rating': None, 'rating_count': None }

def apply_filter(retrieved_values, filter_range):
    """
    Applies a min/max filter to a list of retrieved values.

    Args:
        retrieved_values (list): List of numeric values or None.
        filter_range (list or None): A list [min_val, max_val] or None.
                                     min_val or max_val can be None.

    Returns:
        list: A list of indices from retrieved_values that satisfy the filter.
    """
    if not filter_range:
        return list(range(len(retrieved_values)))

    min_val_str, max_val_str = filter_range
    min_val = float(min_val_str) if min_val_str is not None else None
    max_val = float(max_val_str) if max_val_str is not None else None

    indices = []
    for i, value in enumerate(retrieved_values):
        if value is None:  # Skip items with no value for this attribute
            # Or, decide if None should pass if min_val/max_val is None
            # For now, items with None value won't pass any specific range check
            continue 
        
        passes_min = (min_val is None) or (value >= min_val)
        passes_max = (max_val is None) or (value <= max_val)
        
        if passes_min and passes_max:
            indices.append(i)
    return indices

def special_case_filter(case_dict, retrieved_indices, metadata):
    """
    Process the special case filter from the input dictionary.
    Returns a dictionary with keys 'price', 'rating', and 'rating_count'.
    """
    retrieved_prices = []
    for i in retrieved_indices:
        if i != -1:
            price_str = metadata[i].get('price')
            price_str = price_str.replace('$', '').replace('₹', '').replace(',', '').strip()
            try:
                retrieved_prices.append(float(price_str))
            except (ValueError, TypeError):
                retrieved_prices.append(None)

    retrieved_ratings = []
    for i in retrieved_indices:
        if i != -1:
            rating_str = metadata[i].get('rating')
            try:
                retrieved_ratings.append(float(rating_str))
            except (ValueError, TypeError):
                retrieved_ratings.append(None)

    retrieved_rating_counts = []
    for i in retrieved_indices:
        if i != -1:
            rating_count_str = metadata[i].get('rating_count')
            try:
                retrieved_rating_counts.append(float(rating_count_str))
            except (ValueError, TypeError):
                retrieved_rating_counts.append(0)

    # Apply filters
    price_indices = apply_filter(retrieved_prices, case_dict.get('price'))
    rating_indices = apply_filter(retrieved_ratings, case_dict.get('rating'))
    rating_count_indices = apply_filter(retrieved_rating_counts, case_dict.get('rating_count'))
    
    # Combine indices
    combined_indices = set(price_indices) & set(rating_indices) & set(rating_count_indices)
    combined_length = len(combined_indices)
    filtered_out = set(range(len(retrieved_prices))) - combined_indices
    final_indices = [retrieved_indices[i] for i in combined_indices] + [retrieved_indices[i] for i in filtered_out]
    return final_indices, combined_length

# ------------------------
# Test harness with sample inputs
# ------------------------
if __name__ == '__main__':
    test_cases = [
        { 'special': 'with price range of 100 to 200 dollars, rating of 4.7 stars' },
        { 'special': 'rating of at least 3.5' },
        { 'special': 'rating count between 50 and 200 reviews, price up to 150 dollars' },
        { 'special': 'price between 10 and 50, rating of 4 stars, rating count at least 100' },
        { 'special': 'price less than 75 dollars' },
        { 'special': 'rating count over 500 reviews' },
        { 'special': '' },  # empty input
        # {}
    ]

    # for idx, case in enumerate(test_cases, 1):
    #     result = special_case_split(case, client, model)
    #     print(f"Test {idx}: Input: '{case['special']}' -> Result: {json.dumps(result, indent=2)}")
    #     k = special_case_filter(result, If[order], meta)
    #     print(f"Filtered indices: {k}")
    #     print(f"Filtered results: {[meta[i] for i in k]}")
    #     time.sleep(1)  # Sleep to avoid hitting rate limits
