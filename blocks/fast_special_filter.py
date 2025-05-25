import json
from typing import List, Dict, Any, Tuple
import re
import google.generativeai as genai

# Initialize Gemini model
genai.configure(api_key='AIzaSyBS2npulOMMZ9WRj7b-UpoYHXVSa0Jju4o')
model = genai.GenerativeModel('gemini-2.0-flash')

def parse_spec_query(query: str, model = model) -> Dict[str, Any]:
    """
    Use the Gemini model to parse a free-form query about numeric specifications into a structured filter.

    Returns a dict:
      {
        "feature": str,
        "operator": str,
        "value": float or Tuple[float, float]
      }
    """
    prompt = f"""
You are a parser that extracts a numerical filter from a user query.

Examples:
- "equal to 10 watts"         -> {{"feature": "power_watts", "operator": "=", "value": 10}}
- "greater than 100"          -> {{"feature": "power_watts", "operator": ">", "value": 100}}
- "less than 5"               -> {{"feature": "power_watts", "operator": "<", "value": 5}}
- "between 20 and 50 watts"   -> {{"feature": "power_watts", "operator": "between", "value": [20, 50]}}

Parse the following query into JSON with keys: feature, operator, value.
Respond only with the JSON.

Query: "{query}"
"""
    raw = model.generate_content([prompt]).text
    start = raw.find('{')
    end = raw.rfind('}') + 1
    return json.loads(raw[start:end])


def batch_extract_relevant_spec(
    descriptions: List[str],
    feature_name: str,
    model = model,
    batch_size: int = 10
) -> List[Dict[str, Any]]:
    """
    Extract only the specified numerical feature from product descriptions in batches.

    Args:
        descriptions: List of product description strings.
        feature_name: The normalized spec name to extract.
        model: Initialized Gemini model instance.
        batch_size: Number of descriptions per batch.

    Returns:
        A list of dicts:
          [
            {"description": str, feature_name: value or None},
            ...
          ]
    """
    results: List[Dict[str, Any]] = []
    total = len(descriptions)
    for i in range(0, total, batch_size):
        batch = descriptions[i : i + batch_size]
        prompt = f"""
Extract only the '{feature_name}' numerical value from each product description below.
Return a JSON array where each element has keys:
  "description": original text,
  "{feature_name}": numeric value or null if not present

Descriptions:
""" + "\n".join(f"- {d}" for d in batch)
        raw = model.generate_content([prompt]).text
        start = raw.find('[')
        end = raw.rfind(']') + 1
        fragment = raw[start:end] if start != -1 and end != -1 else raw
        try:
            arr = json.loads(fragment)
        except json.JSONDecodeError:
            # fallback: manual regex extraction
            arr = []
            unit_map = {
                'power_watts': r"(\d+(?:\.\d+)?)\s*watts",
                'battery_mah': r"(\d+(?:\.\d+)?)\s*mAh",
                'capacity_liters': r"(\d+(?:\.\d+)?)\s*(?:liters|L)"
            }
            pattern = unit_map.get(feature_name)
            for d in batch:
                value = None
                if pattern:
                    m = re.search(pattern, d, re.IGNORECASE)
                    if m:
                        value = float(m.group(1))
                arr.append({"description": d, feature_name: value})
        results.extend(arr)
    return results

def filter_to_query(query, meta, indices, batch_size = 10) -> str:
    
    descriptions = []
    for i in indices:
        descriptions.append(meta[i]['text_input'])
    parsed_dict = parse_spec_query(query, model)
    feature = parsed_dict['feature']
    operator = parsed_dict['operator']
    value = parsed_dict['value']

    feature_searchs = batch_extract_relevant_spec(descriptions, feature, model, batch_size)
    if operator == '=':
        scores = [abs(d[feature]/value - 1) if d[feature] is not None else 1 for d in feature_searchs]
    elif operator == '>':
        scores = [0 if (d[feature] is not None and d[feature] > value) else 1 for d in feature_searchs]
    elif operator == '<':
        scores = [0 if (d[feature] is not None and d[feature] < value) else 1 for d in feature_searchs]
    elif operator == 'between':
        scores = [0 if (d[feature] is not None and d[feature] > value[0] and d[feature] < value[1]) else 1 for d in feature_searchs]
    
    out = {}
    for i, score in zip(indices, scores):
        out[i] = score
    return out

def parse_split_query(query: str, model = model) -> Dict[str, Any]:
    """
    Use the Gemini model to parse a free-form query about numeric specifications into a structured filter.
    Rule: consider all numeric specifications in the query except price, rating, no of ratings or rating count or descount which are not considered numeric specifications. And are managed seperately.
    Returns a list of strings, each representing a numeric filter extracted from the query:
      
    """
    prompt = f"""
You are a parser that extracts a numerical filter from a user query.
Rule: consider all numeric specifications in the query except price, rating, no of ratings or rating count or descount which are not considered numeric specifications. And are managed seperately.
Examples:
- Input: "greater than 10 watts and less than 50 mAh"
  Output: ["greater than 10 watts", "less than 50 mAh"]

- Input: "between 5 and 20 liters"
  Output: ["between 5 and 20 liters"]

- Input: "show devices under 1000 rupees"
  Output: []

- Input: "equal to 100 watts, greater than 200 mAh and less than 5 liters"
  Output: ["equal to 100 watts", "greater than 200 mAh", "less than 5 liters"]

- Input: "Looking for an Apple smartphone with 8GB RAM and battery greater than 3000 mAh"
  Output: ["greater than 3000 mAh"]

Now split the following query, and ignore any text that does not specify a numeric comparison: the following query, and ignore any text that does not specify a numeric comparison:
"{query}"
"""
    raw = model.generate_content([prompt]).text
    # extract JSON array
    start = raw.find('[')
    end = raw.rfind(']') + 1
    json_str = raw[start:end] if start != -1 and end != -1 else '[]'
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return []

def rerank_with_spec_filter(
    query_list: List[str],
    meta: List[Dict[str, Any]],
    indices: List[int],
    batch_size: int = 10,
) -> List[int]:
    """
    Rerank the given indices based on a specification filter parsed from the query.

    Args:
        query: The user query containing numeric specifications.
        meta: Metadata for all items.
        indices: Indices of items to rerank.
        model: Initialized Gemini model instance.

    Returns:
        A list of indices sorted by the specification filter.
    """
    filter_scores = []
    for feature_query in query_list:
        filter_scores.append(filter_to_query(feature_query, meta, indices, batch_size))
    # add all scores together
    combined_scores = {i: 0 for i in indices}
    for score_dict in filter_scores:
        for i, score in score_dict.items():
            combined_scores[i] += score
    # Sort indices based on combined scores
    sorted_indices = sorted(combined_scores, key=lambda x: combined_scores[x])
    return sorted_indices



# ---------- Tests ----------
if __name__ == "__main__":
    # Test parse_spec_query
    f1 = parse_spec_query("greater than 100 watts", model)
    print("Parsed filter:", f1)

    # Realistic descriptions for feature extraction tests
    descriptions = [
        "Smartphone A: battery 3000 mAh, power consumption 5 watts, capacity 1.5 liters",
        "Phone B: battery 4500 mAh and capacity 2 liters",
        "Gadget C uses 10 watts, capacity 1 liter",
        "Widget D has no battery spec but uses 3.3 watts",
        "Appliance E capacity 0.75 L, battery 2000 mAh"
    ]

    battery_specs = batch_extract_relevant_spec(descriptions, "battery_mah", model)
    power_specs = batch_extract_relevant_spec(descriptions, "power_watts", model)
    capacity_specs = batch_extract_relevant_spec(descriptions, "capacity_liters", model)

    print("Battery specs:", battery_specs)
    print("Power specs:", power_specs)
    print("Capacity specs:", capacity_specs)
