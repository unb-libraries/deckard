"""Provides standard responses for the LLM."""
def fail_response() -> str:
    """Returns the standard LLM fail response."""
    return "Sorry, I could not find relevant information to address this question."

def error_response() -> str:
    """Returns the standard LLM error response."""
    return "Sorry, I am having trouble answering questions right now."
