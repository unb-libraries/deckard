"""Provides standard prompts for the LLM."""
from .responses import fail_response

def get_old_context_only_prompt() -> str:
    """Returns the prompt that instructs the LLM to only respond based on context.

    Returns:
        str: The prompt.
    """
    return """### Instruction:
    Read the context below and respond with an answer to the question. If the question cannot be answered based on
    the context alone or the context does not explicitly say the answer to the question, write only "%s". Do not explain why.

    ### Input:
    Context: {context}

    Question: {query}

    Response: """ % (fail_response())

def get_context_only_prompt() -> str:
    """Returns the prompt that instructs the LLM to only respond based on context.

    Returns:
        str: The prompt.
    """
    return """<|start_header_id|>system<|end_header_id|>
You are a factual AI assistant.
Only answer user questions using the provided context.
Do not use any outside knowledge.

Your answers must follow these rules:

Do not include any introductory phrases like:

"Based on the context..."

"According to the context..."

"The answer is..."

If the answer is not completely found in the context, reply with:
"%s" — and say nothing else.

Keep responses direct and concise. No elaboration or explanation unless it is in the context.
<|eot_id|>

<|start_header_id|>user<|end_header_id|> 
Question :

{query}

Context :

{context}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>""" % (fail_response())

def get_old_context_plus_prompt() -> str:
    """Returns the prompt that instructs the LLM to respond however it can.

    Returns:
        str: The prompt.
    """
    return """### Instruction:
    Read the context below and respond with an answer to the question. Respond only with information you learn within the context. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    ### Input:
    Context: {context}

    Question: {query}

    Response: """

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

    Response: """

def get_qa_prompt(qa_sets) -> str:

    return """### Instruction:
    Read the context below and respond with an answer to the question. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    ### Input:
    Context: {context}

    Question: {query}

    Response: """