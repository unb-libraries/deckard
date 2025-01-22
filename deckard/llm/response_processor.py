"""Provides the ResponseProcessor class."""
class ResponseProcessor:
    """Processes the response from the LLM.

    Args:
        response (str): The response to process.

    Attributes:
        response (str): The response to process.
    """
    def __init__(self, response: str) -> None:
        self.response = response
        if self.response is None or self.response == '':
            return
        self._set_clean_response()

    def _set_clean_response(self) -> None:
        self.response = self.response.strip()

    def get_clean_response(self) -> str:
        """Returns the clean-safe response.

        Returns:
            str: The clean response.
        """
        return self.response
