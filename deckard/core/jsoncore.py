"""Provides JSON functions."""
import json
import re

JSON_DUMP_INDENT = 4

def json_dumper(data: dict, pretty: bool=True, sort_keys: bool=False) -> str:
    """Dumps a dictionary to a JSON string.

    Args:
        data (dict): The dictionary to dump.
        pretty (bool): Whether to pretty print the JSON.
        sort_keys (bool): Whether to sort the keys.

    Returns:
        str: The JSON string.
    """
    if not pretty:
        return json.dumps(data, sort_keys=sort_keys)
    return json.dumps(
        data,
        indent=JSON_DUMP_INDENT,
        sort_keys=sort_keys
    )

def extract_first_json_block(content, data_type, logger):
    """Extracts the first JSON block from the content.
    
    Args:
        content (str): The content to extract from.
        data_type (str): The type of data (used in messaging).
        logger (Logger): The logger to use.

    Returns:
        dict: The extracted JSON. None if not found.
    """
    try:
        json_pattern = r'\{.*?\}'
        matches = re.findall(json_pattern, content, re.DOTALL)
        
        if not matches:
            logger.error(f"Error parsing {data_type}: No JSON found")
            return None
        
        for match in matches:
            try:
                parsed_json = json.loads(match)
                return parsed_json
            except json.JSONDecodeError as je:
                logger.error(f"Error parsing JSON: {je}")
                continue 

        logger.error(f"Error parsing {data_type}: No valid JSON found")
        return None

    except Exception as e:
        logger.error(f"Error: {e}")
        return None
