"""Provides functions for working with YAML files."""
import yaml

def load_yaml(filepath: str) -> dict:
    """Loads a YAML file into a dictionary.

    Args:
        filepath (str): The path to the YAML file.

    Returns:
        dict: The YAML file as a dictionary.
    """
    return yaml.safe_load(
        open(
            filepath,
            encoding='utf-8'
        )
    )
