import google.generativeai as genai
import os # Added for example usage path check

# Initialize Gemini model
api_key='AIzaSyBS2npulOMMZ9WRj7b-UpoYHXVSa0Jju4o'
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemma-3-12b-it')

def generate_user_pref_query(base_product_name: str, logfile: str) -> str:
    """
    Reads the user activity log and uses a two-step process with the Gemini model
    to generate a concise user preference query.
    Step 1: Analyze logs to identify preferences and suggest a query (internal thought process).
    Step 2: Refine the output of Step 1 into a single, concise search query.

    Args:
      base_product_name: The type of product (e.g., "smartphone", "headphones").
      logfile: Path to the text log file (logs.txt).

    Returns:
      A short single-line search query reflecting user preferences.
    """
    # Read raw logs text
    with open(logfile, 'r', encoding='utf-8') as f:
        logs_text = f.read().strip()

    # ----- Step 1: Initial Analysis and Preference Identification -----
    prompt1 = f"""
    You are a personal shopping assistant. Below is the user’s raw activity log:
    {logs_text}

    Based on this history, thoroughly analyze the user's likely preferences for a new '{base_product_name}'.
    Consider their preferred brands, favored colors, typical price ranges, ratings, and any other repeated patterns.
    Describe these preferences in a few sentences and explicitly suggest what a good search query might look like based on your analysis. This is an intermediate step; the final query will be extracted later.
    Example of your output for this step:
    "The user seems to prefer Apple products, particularly in Space Gray or Silver. They have purchased items around $1000. For a new smartphone, a good query might be 'Apple smartphone Space Gray under $1200'."
    """

    analysis_response = model.generate_content([prompt1])
    detailed_analysis = analysis_response.text.strip()
    # print(f"---- Intermediate Analysis for {base_product_name}: ----\n{detailed_analysis}\n----------------------------------") # Optional: for debugging

    # ----- Step 2: Strict Query Formulation from Analysis -----
    prompt2 = f"""
    You are a query refinement assistant. Based on the following analysis of user preferences for a '{base_product_name}':

    Analysis Provided:
    {detailed_analysis}

    Your task is to extract or formulate ONLY ONE concise search query from the Analysis Provided.
    This query should include the product type ('{base_product_name}') and the most salient preferences (e.g., brand, color, price) identified in the analysis.

    ### Example of how to process Analysis to Output:
    Analysis Provided: The user seems to prefer Philips brand for irons, often looks at blue items, and has searched for items under 3000 rs. A good query might be "blue Philips iron box under 3000 rs".
    Product: 'iron box'
    Output: "blue Philips iron box under 3000 rs"

    Analysis Provided: User likes Sony headphones, often black, and has bought items around $300-$400. A good query could be "black Sony headphones around $350".
    Product: 'headphones'
    Output: "black Sony headphones around $350"

    IMPORTANT INSTRUCTIONS FOR YOUR FINAL OUTPUT:
    1. Your response MUST be ONLY the concise search query itself.
    2. DO NOT include any introductory phrases (like "Here is the query:", "The query is:", "Based on the analysis, the query is:").
    3. DO NOT include any explanations, apologies, or any text whatsoever other than the generated search query.
    4. If the determined query is "Silver smartphone under $500", your output must be exactly: Silver smartphone under $500
    Ensure your output is ONLY the query string.
    """

    final_query_response = model.generate_content([prompt2])
    return final_query_response.text.strip()

# Example usage (commented out for notebook execution):
# log_file_path_example = '..\\logs.txt' # Adjust path as needed
# if os.path.exists(log_file_path_example):
#     query_smartphone = generate_user_pref_query('smartphone', log_file_path_example)
#     print(f"Generated Query for smartphone: {query_smartphone}")

#     query_headphones = generate_user_pref_query('headphones', log_file_path_example)
#     print(f"Generated Query for headphones: {query_headphones}")

#     query_washing_machine = generate_user_pref_query('washing machine', log_file_path_example)
#     print(f"Generated Query for washing machine: {query_washing_machine}")
# else:
#     print(f"Log file not found at {os.path.abspath(log_file_path_example)} for example usage.")
