"""Provides standard responses for the LLM."""
def fail_response() -> str:
    """Returns the standard LLM fail response."""
    return "Sorry, I had trouble answering this question based on the information I found."

def error_response() -> str:
    """Returns the standard LLM error response."""
    return "Sorry, I am having trouble answering questions right now."
