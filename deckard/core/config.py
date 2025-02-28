"""Provides access to the configuration file and its contents."""
from os.path import join as path_join
from .yaml import load_yaml

def get_config_as_dict() -> dict:
    """Gets the configuration file as a dictionary.

    Returns:
        dict: The configuration file as a dictionary.
    """
    return load_yaml("config.yml")

def get_api_config() -> dict:
    """Gets the API configuration from the configuration file.

    Returns:
        dict: The API configuration.
    """
    return get_config_as_dict()['api']

def get_api_llm_config() -> dict:
    """Gets the LLM configuration from the configuration file.

    Returns:
        dict: The LLM configuration.
    """
    return get_api_config()['llm']['model']

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
    return f"Available RAG pipelines: {get_rag_pipeline_names()}"

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

def get_gpu_lockfile() -> str:
    """Gets the GPU lockfile from the configuration file.

    Returns:
        str: The GPU lockfile.
    """
    data_dir = get_data_dir()
    lockfile = get_config_as_dict()['api']['gpu_lock_file']
    return path_join(data_dir, lockfile)

def get_api_gpu_exclusive_mode() -> bool:
    """Gets the GPU exclusive mode from the configuration file.

    Returns:
        bool: The GPU exclusive mode.
    """
    return get_api_config()['gpu_exclusive_mode']

def get_client_uri() -> str:
    """Gets the client URI from the configuration file.

    Returns:
        str: The client URI.
    """
    return get_config_as_dict()['client']['uri']

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

def get_client_keypair() -> tuple:
    """Gets the client keypair from the configuration file.

    Returns:
        tuple: The client keypair.
    """
    return get_config_as_dict()['client']['pub_key'], get_config_as_dict()['client']['priv_key']

def get_client_user_agent() -> str:
    """Gets the HTTP user agent from the configuration file.

    Returns:
        str: The HTTP user agent.
    """
    return get_config_as_dict()['client']['user_agent']

def get_client_timeout() -> int:
    """Gets the client timeout from the configuration file.

    Returns:
        int: The client timeout.
    """
    return int(get_config_as_dict()['client']['timeout'])

def get_slack_config() -> dict:
    """Gets the Slack configuration from the configuration file.

    Returns:
        dict: The Slack configuration.
    """
    return get_config_as_dict()['slackbot']
