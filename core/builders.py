from core.config import get_workflow_db
from core.config import get_workflow_encoder
from core.config import get_workflows
from core.prompts import CONTEXT_ONLY_PROMPT
from core.prompts import CONTEXT_PLUS_PROMPT
from core.RagStack import RagStack
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

def build_rag_stacks(log):
    stacks = {}
    workflows = get_workflows()
    for w in workflows.values():
        c = __import__(
            'core.' + w['rag']['stack']['classname'],
            fromlist=['']
        )
        rs = getattr(c, w['rag']['stack']['classname'])
        stacks[w['name']] = rs(w['rag'], log)
    return stacks

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
