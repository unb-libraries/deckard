from core.config import get_workflow_db
from core.config import get_workflow_encoder
from core.config import get_workflows
from core.prompts import CONTEXT_ONLY_PROMPT
from core.prompts import CONTEXT_PLUS_PROMPT
from core.RagStack import RagStack
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

def build_query_stacks(log):
    stacks = {}
    workflows = get_workflows()
    for w in workflows.values():
        stacks[w['name']] = RagStack(w['name'], log)
    return stacks

def build_rag_encoders(log):
    transformers = {}
    workflows = get_workflows()
    for w in workflows.values():
        transformer = get_workflow_encoder(w['name'], log)
        transformers[w['name']] = transformer
    return transformers

def build_rag_databases(log):
    dbs = {}
    workflows = get_workflows()
    for w in workflows.values():
        database = get_workflow_db(w['name'], log)
        dbs[w['name']] = database
    return dbs

def build_llm_chains(app, llm):
    chains = {}
    chains['chain-context-only'] = build_llm_chain(
        llm,
        CONTEXT_ONLY_PROMPT()
    )
    chains['chain-context-plus'] = build_llm_chain(
        llm,
        CONTEXT_PLUS_PROMPT()
    )
    return chains

def build_llm_chain(llm, template):
    prompt = PromptTemplate(
        input_variables=["context", "query"],
        template=template,
    )
    return LLMChain(llm=llm, prompt=prompt)
