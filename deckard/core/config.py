"""Provides access to the configuration file and its contents."""
from .yaml import load_yaml

def get_config_as_dict() -> dict:
    """Gets the configuration file as a dictionary.

    Returns:
        dict: The configuration file as a dictionary.
    """
    return load_yaml("config.yml")

def get_api_llm_config() -> dict:
    """Gets the LLM configuration from the configuration file.

    Returns:
        dict: The LLM configuration.
    """
    return get_config_as_dict()['api']['llm']['model']

def get_http_user_agent() -> str:
    """Gets the HTTP user agent from the configuration file.

    Returns:
        str: The HTTP user agent.
    """
    return ('Deckard/0.1 Mozilla/5.0 (Windows NT 10.0; Win64; x64) ',
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 ',
            'Safari/537.3'
    )

def get_rag_pipelines() -> dict:
    """Gets the RAG pipelines from the configuration file.

    Returns:
        dict: The RAG pipelines.
    """
    return get_config_as_dict()['rag']

def get_rag_pipeline_names() -> str:
    """Gets the names of all RAG pipelines from the configuration file.

    Returns:
        str: The names of the RAG pipelines.
    """
    return ', '.join(get_rag_pipelines().keys())

def available_rag_pipelines_message() -> str:
    """Gets a message with the names of all RAG pipelines from the configuration file.

    Returns:
        str: The message.
    """
    return("Available RAG pipelines: %s", get_rag_pipeline_names())

def get_rag_pipeline(pipeline_id: str) -> dict:
    """Gets a RAG pipeline from the configuration file.

    Args:
        pipeline_id (str): The ID of the RAG pipeline.

    Returns:
        dict: The RAG pipeline.
    """
    w = get_rag_pipelines()
    if pipeline_id not in w:
        return None
    return w[pipeline_id]

def get_data_dir() -> str:
    """Gets the data directory from the configuration file.

    Returns:
        str: The data directory.
    """
    return get_config_as_dict()['data_dir']

def get_api_port() -> int:
    """Gets the API port from the configuration file.

    Returns:
        int: The API port.
    """
    return int(get_config_as_dict()['api']['port'])

def get_api_host() -> str:
    """Gets the API hostname from the configuration file.

    Returns:
        str: The API host.
    """
    return get_config_as_dict()['api']['host']
