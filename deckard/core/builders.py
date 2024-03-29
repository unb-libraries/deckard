"""Provides the builders for the core components of Deckard."""
from logging import Logger

from langchain_community.llms import LlamaCpp
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from deckard.llm import get_context_only_prompt, get_context_plus_prompt
from .config import get_rag_pipelines

def build_rag_stacks(log: Logger) -> dict:
    """Builds the RAG stacks from the configuration.

    Args:
        log (Logger): The logger for the RAG stacks.

    Returns:
        dict: The RAG stacks.
    """
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

def build_llm_chains(llm: LlamaCpp) -> list[LLMChain]:
    """Builds the LLM chains from the LLM.

    Args:
        llm (LlamaCpp): The LLM to build the chains from.

    Returns:
        list[LLMChain]: The LLM chains.
    """
    chains = {}
    chains['chain-context-only'] = build_llm_chain(
        llm,
        get_context_only_prompt()
    )
    chains['chain-context-plus'] = build_llm_chain(
        llm,
        get_context_plus_prompt()
    )
    return chains

def build_llm_chain(llm: LlamaCpp, template: str) -> LLMChain:
    """Builds an LLM chain from the LLM and template.

    Args:
        llm (LlamaCpp): The LLM to build the chain from.
        template (str): The query template for the chain.

    Returns:
        LLMChain: The LLM chain.
    """
    prompt = PromptTemplate(
        input_variables=["context", "query"],
        template=template,
    )
    return LLMChain(llm=llm, prompt=prompt)
