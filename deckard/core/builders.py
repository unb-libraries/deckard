from .config import get_rag_pipelines
from deckard.llm import CONTEXT_ONLY_PROMPT
from deckard.llm import CONTEXT_PLUS_PROMPT
from langchain_community.llms import LlamaCpp
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from logging import Logger

def build_rag_stacks(log: Logger) -> dict:
    stacks = {}
    pipelines = get_rag_pipelines()
    for w in pipelines.values():
        c = __import__(
            w['rag']['stack']['module_name'],
            fromlist=['']
        )
        rs = getattr(c, w['rag']['stack']['class_name'])
        stacks[w['name']] = rs(w['rag'], log)
    return stacks

def build_llm_chains(llm: LlamaCpp) -> LLMChain:
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

def build_llm_chain(llm: LlamaCpp, template: str) -> LLMChain:
    prompt = PromptTemplate(
        input_variables=["context", "query"],
        template=template,
    )
    return LLMChain(llm=llm, prompt=prompt)
