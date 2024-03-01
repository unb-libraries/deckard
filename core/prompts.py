from core.responses import fail_response

def CONTEXT_ONLY_PROMPT() -> str:
    return """### Instruction:
    Read the context below and respond with an answer to the question. If the question cannot be answered based on
    the context alone or the context does not explicitly say the answer to the question, write "%s"

    ### Input:
    Context: {context}

    Question: {query}

    Response:""" % (fail_response())

def CONTEXT_PLUS_PROMPT() -> str:
    return """### Instruction:
    Read the context below and respond with an answer to the question. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    ### Input:
    Context: {context}

    Question: {query}

    Response:"""
