import yaml

def get_config_as_dict():
    return yaml.safe_load(open("config.yml"))

def get_api_llm_config():
    return get_config_as_dict()['api']['llm']['model']

def get_http_user_agent():
    return 'Deckard/0.1 Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

def get_rag_pipelines():
    return get_config_as_dict()['rag']

def get_rag_pipeline_names():
    return ', '.join(get_rag_pipelines().keys())

def get_rag_pipeline(id: str):
    w = get_rag_pipelines()
    if id not in w:
        return None
    return w[id]

def get_data_dir():
    return get_config_as_dict()['data_dir']

def get_api_port():
    return get_config_as_dict()['api']['port']

def get_api_host():
    return get_config_as_dict()['api']['host']
