"""Provides standard prompts for the LLM."""
from .responses import fail_response

def get_old_context_only_prompt() -> str:
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

    Response: """ % (fail_response())

def get_context_only_prompt() -> str:
    """Returns the prompt that instructs the LLM to only respond based on context.

    Returns:
        str: The prompt.
    """
    return """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful AI assistant for answering questions based on user provided context. You will only use the provided text to answer the questions. Do not say "Based on the provided text," or "According to the text," or anything similar. Just provide the answer. Do not provide personal opinions or biases. If the answer is not available in the text you will answer as "%s" <|eot_id|><|start_header_id|>user<|end_header_id|>

Please answer the following question based on the text I am providing only. 

Question :

{query}

Text :

{context}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>""" % (fail_response())

def get_old_context_plus_prompt() -> str:
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