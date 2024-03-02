"""Provides standard prompts for the LLM."""
from .responses import fail_response

def get_context_only_prompt() -> str:
    """Returns the prompt that instructs the LLM to only respond based on context.

    Returns:
        str: The prompt.
    """
    return """### Instruction:
    Read the context below and respond with an answer to the question. If the question cannot be answered based on
    the context alone or the context does not explicitly say the answer to the question, write "%s"

    ### Input:
    Context: {context}

    Question: {query}

    Response:""" % (fail_response())

def get_context_plus_prompt() -> str:
    """Returns the prompt that instructs the LLM to respond however it can.

    Returns:
        str: The prompt.
    """
    return """### Instruction:
    Read the context below and respond with an answer to the question. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    ### Input:
    Context: {context}

    Question: {query}

    Response:"""
