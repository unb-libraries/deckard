import yaml

def get_config_as_dict():
    return yaml.safe_load(open("config.yml"))

def get_api_llm_config():
    return get_config_as_dict()['api']['llm']['model']

def get_http_user_agent():
    return 'Deckard/0.1 Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

def get_workflows():
    return get_config_as_dict()['workflows']

def get_workflow_names():
    return ', '.join(get_workflows().keys())

def get_workflow(id):
    w = get_workflows()
    if id not in w:
        return None
    return w[id]

def get_data_dir():
    return get_config_as_dict()['data_dir']

def get_api_port():
    return get_config_as_dict()['api']['port']

def get_api_host():
    return get_config_as_dict()['api']['host']

def get_workflow_context_rag_conf(id):
    w = get_workflow(id)
    if w is None:
        return None
    return w['rag']

def get_workflow_collectors(id, log):
    w = get_workflow(id)
    if w is None:
        return None
    for c in w['collectors']:
        m = __import__(
            'collectors.' +
                c['class'],
            fromlist=['']
        )
        cc = getattr(m, c['class'])
        yield cc(log)

def get_workflow_db(id, log, create_if_not_exists=False):
    w = get_workflow(id)
    if w is None:
        return None
    m = __import__(
        'vectordatabases.' +
            w['database']['class'],
        fromlist=['']
    )
    dc = getattr(m, w['database']['class'])
    return dc(w['database']['name'], log, create_if_not_exists)

def get_workflow_context_db(id, log, create_if_not_exists=False):
    w = get_workflow(id)
    if w is None:
        return None
    m = __import__(
        'contextdatabases.' +
            w['context_database']['class'],
        fromlist=['']
    )
    dc = getattr(m, w['context_database']['class'])
    return dc(w['context_database']['name'], log, create_if_not_exists)

def get_workflow_transformer(id, log):
    w = get_workflow(id)
    if w is None:
        return None
    m = __import__(
        'datatransformers.' +
            w['transformer']['class'],
        fromlist=['']
    )
    tc = getattr(m, w['transformer']['class'])
    return tc(
        w['transformer']['model'],
        log
    ).get()

def get_workflow_chunker(id, log):
    w = get_workflow(id)
    if w is None:
        return None
    m = __import__(
        'chunkers.' +
            w['chunker']['class'],
        fromlist=['']
    )
    cc = getattr(m, w['chunker']['class'])
    return cc(log)

def get_workflow_rag_context_builder(id, log):
    w = get_workflow(id)
    if w is None:
        return None
    m = __import__(
        'contextbuilders.' +
            w['rag']['context_builder']['class'],
        fromlist=['']
    )
    cb = getattr(m, w['rag']['context_builder']['class'])
    return cb(log)
