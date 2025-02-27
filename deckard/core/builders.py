from logging import Logger
from langchain_community.llms import LlamaCpp
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

from deckard.llm import get_context_only_prompt, get_context_plus_prompt, response_addresses_query_prompt, malicious_classification_prompt, explode_query_prompt, summarize_response_prompt

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

def build_llm_chains(llm: LlamaCpp) -> list[RunnableSequence]:
    """Builds the LLM chains from the LLM.

    Args:
        llm (LlamaCpp): The LLM to build the chains from.

    Returns:
        list[RunnableSequence]: The LLM chains.
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
    chains['chain-verify-response'] = build_llm_chain(
        llm,
        response_addresses_query_prompt()
    )
    chains['compound'] = build_llm_chain(
        llm,
        explode_query_prompt()
    )
    chains['malicious'] = build_llm_chain(
        llm,
        malicious_classification_prompt()
    )
    chains['summarizer'] = build_llm_chain(
        llm,
        summarize_response_prompt()
    )
    return chains

def build_llm_chain(llm: LlamaCpp, template: str) -> RunnableSequence:
    """Builds an LLM chain from the LLM and template.

    Args:
        llm (LlamaCpp): The LLM to build the chain from.
        template (str): The query template for the chain.

    Returns:
        RunnableSequence: The LLM chain sequence.
    """
    prompt = PromptTemplate(
        input_variables=["context", "query"],
        template=template,
    )
    return prompt | llm
