"""Provides JSON functions."""
import json

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
