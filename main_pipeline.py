# main_pipeline.py
"""
Pipeline entrypoint with debug logging and fixed delay after each step.
"""

import logging
from pydoc import text
import time
from blocks import query_manipulations, special_case_handler, image_extractions, retrival,extract_tags
from blocks import voyage_rerank
from blocks import fast_special_filter
from blocks import history_pref

# Configure logging
def setup_logger():
    logger = logging.getLogger("main_pipeline")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger

logger = setup_logger()

current_text = 'blue iron'
back_bone = 'iron'
retrieved_idx = None
meta = None
img_weight = 0.3
text_weight = 0.7

def delay():
    """Fixed delay between steps."""
    logger.debug("Adding delay between steps")
    time.sleep(1)

def main_pipeline(modification_text: str, reset: bool, image_path: str = None) -> int:
    """
    Main pipeline to process the modification text and current text.
    """
    global current_text
    global back_bone
    global retrieved_idx
    global meta, img_weight, text_weight
    
    logger.debug(f"Starting main_pipeline with: modification_text='{modification_text}', reset={reset}, image_path={image_path}")
    logger.debug(f"Initial state: current_text='{current_text}', back_bone='{back_bone}'")
    
    query_dict = {}
    special_case_dict = None
    conflict = False
    final_out = None
    filter_list = fast_special_filter.parse_split_query(modification_text)
    if reset:
        logger.debug("Reset is True: extracting base description")
        intent = image_extractions.intention(image_path, modification_text)
        logger.debug(f"Intent result: {intent}")
        
        if intent['intent'] == 1:
            logger.debug("Special intent detected")
            image_path = None
            current_text = intent['recommendations_query']
            logger.debug(f"Intent is special, current_text is now: {current_text}")
        else:
            logger.debug("No special intent, proceeding with image extraction")
        if intent['intent'] == 1:
            img_weight = 0
            text_weight = 1
        else:
            img_weight = 0.3
            text_weight = 0.7
        if image_path:
            logger.debug(f"Extracting description from image: {image_path}")
            back_bone, current_text = image_extractions.discription(image_path)
            logger.debug(f"Image description extracted: back_bone='{back_bone}', current_text='{current_text}'")
        else:
            logger.debug("No image path, extracting from text")
            back_bone, current_text = image_extractions.text_split(current_text)
            logger.debug(f"Text split: back_bone='{back_bone}', current_text='{current_text}'")
        modification_text = history_pref.generate_user_pref_query(back_bone,'./logs.txt')

    if image_path:
        logger.debug(f"Modifying query based on image: {image_path}")
        modification_text = image_extractions.modify_query(image_path, modification_text)
        logger.debug(f"Modified query: '{modification_text}'")
        delay()
        
    if modification_text:
        logger.debug(f"Splitting query: '{modification_text}'")
        query_dict = query_manipulations.split_query(modification_text)
        logger.debug(f"Query dict after splitting: {query_dict}")
        delay()
    else:
        logger.debug("No modification text provided, query_dict will be empty")
        query_dict = {}
        
    if query_dict.get('general'):
        logger.debug(f"Updating current_text with general query: '{query_dict['general']}'")
        prev_text = current_text
        # current_text = query_manipulations.update_current_text(current_text, query_dict['general'])
        current_text = image_extractions.alternate_current_text(current_text, query_dict['general'])
        logger.debug(f"Text updated: '{prev_text}' -> '{current_text}'")
        delay()
        
    if query_dict.get('special'):
        logger.debug(f"Processing special case from query: {query_dict['special']}")
        special_case_dict = special_case_handler.special_case_split(query_dict, special_case_handler.client, special_case_handler.model)
        logger.debug(f"Special case dictionary: {special_case_dict}")
        delay()
        
    if modification_text:
        logger.debug(f"Checking for conflicts between current text and modification")
        conflict = query_manipulations.conflict_check(current_text, modification_text)
        logger.debug(f"Conflict detected: {conflict}")
        delay()
        
    if conflict or reset:
        logger.debug(f"Retrieving and reranking due to conflict={conflict} or reset={reset}")
        retrieved_idx, meta = retrival.retrieve_and_rerank(image_path=image_path, text_query=back_bone, rank_query=current_text, img_weight=img_weight, text_weight=text_weight, k=200)
        # logger.debug(f"Retrieved {len(retrieved_idx) if retrieved_idx else 0} items")
        
        logger.debug("Reranking with voyage_rerank")
        reranked_idx, meta = voyage_rerank.rerank_products(retrieved_idx, meta, current_text, k=50)
        logger.debug(f"Reranked to {len(reranked_idx) if reranked_idx else 0} items")
        
        if query_dict.get('special'):
            logger.debug(f"Applying special case filtering")
            final_out, le = special_case_handler.special_case_filter(special_case_dict, reranked_idx, meta)
            # logger.debug(f"Final output after special filtering: {len(final_out) if final_out else 0} items")
        else:
            logger.debug("No special filtering applied")
            final_out = reranked_idx
    else:
        logger.debug("No conflict/reset - using rerank_only path")
        reranked_idx, meta = voyage_rerank.rerank_products(retrieved_idx, meta, current_text, k=50)
        # logger.debug(f"Reranked to {len(reranked_idx) if reranked_idx else 0} items")
        
        if query_dict.get('special'):
            logger.debug(f"Applying special case filtering")
            final_out, le = special_case_handler.special_case_filter(special_case_dict, reranked_idx, meta)
            # logger.debug(f"Final output after special filtering: {len(final_out) if final_out else 0} items")
        else:
            logger.debug("No special filtering needed")
            final_out = reranked_idx
    
    # Extract tags from the current text
    logger.debug(f"Extracting tags from current text: '{current_text}'")
    try:
        tags = extract_tags.get_tags(current_text)
        logger.debug(f"Extracted tags: {tags}")
        
        # Add tags to metadata
        for idx in final_out:
            if idx < len(meta):
                meta[idx]['tags'] = tags
    except Exception as e:
        logger.error(f"Error extracting tags: {e}")
            
    logger.debug(f"Pipeline completed. Returning {len(final_out) if final_out else 0} items")

    if len(filter_list) > 0:
        logger.debug(f"Applying fast special filter with {len(filter_list)} filters")
        final_out = fast_special_filter.rerank_with_spec_filter(filter_list, meta, final_out, batch_size=20)

    return final_out, meta

# Display helper
def show_results(result, metadata):
    """
    Display the top 10 results inline in a Jupyter notebook.
    """
    logger.debug(f"Displaying top {min(10, len(result))} results")
    from IPython.display import display, HTML
    html = ['<div style="display: flex; flex-wrap: wrap; gap: 16px;">']
    for i, idx in enumerate(result[:30], start=1):
        item = metadata[idx]
        text = item.get('text_input', '') or repr(item)
        image_path = item.get('image_path')
        img_tag = f'<img src="{image_path}" style="max-width:150px; max-height:150px; display:block; margin:auto;"/>' if image_path else ''
        html.append(
            '<div style="width:200px; border:1px solid #ddd; border-radius:8px; padding:8px;">'
            f'<strong>Result {i}</strong><br/>'
            f'{img_tag}'
            f'<div style="margin-top:8px; font-size:0.9em; line-height:1.2;">{text}</div>'
            '</div>'
        )
    html.append('</div>')
    display(HTML(''.join(html)))

# Test run
if __name__ == '__main__':
    logger.debug("Starting test run")
    result, metadata = main_pipeline(None, True, 'img2.jpg')
    logger.debug(f"Test run completed with {len(result)} results")
    show_results(result, metadata)

