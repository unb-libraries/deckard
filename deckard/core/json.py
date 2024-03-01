import json

JSON_DUMP_INDENT = 4

def json_dumper(data: dict, sort_keys: bool=False) -> str:
    return json.dumps(
        data,
        indent=JSON_DUMP_INDENT,
        sort_keys=sort_keys
    )
