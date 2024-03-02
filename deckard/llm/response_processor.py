"""Provides the ResponseProcessor class."""
class ResponseProcessor:
    """Processes the response from the LLM, including throwing tripwires.

    Args:
        response (str): The response to process.

    Attributes:
        TRIPWIRE_TERMS (list): The terms that will trip the wire.
        response (str): The response to process.
        tripwire_thrown (bool): The tripwire thrown flag.
    """
    TRIPWIRE_TERMS = [
        'fraggle'
    ]

    def __init__(self, response: str) -> None:
        self.response = response
        self.tripwire_thrown = False
        if self.response is None or self.response == '':
            return
        self._set_clean_response()
        self._test_tripwire()

    def _test_tripwire(self) -> None:
        """Tests the response for tripwires."""
        self.tripwire_thrown = False
        for term in self.TRIPWIRE_TERMS:
            if term in self.response:
                self.tripwire_thrown = True

    def _set_clean_response(self) -> None:
        self.response = self.response.strip()

    def was_tripwire_thrown(self) -> bool:
        """Returns the tripwire thrown flag.

        Returns:
            bool: Whether the tripwire was thrown.
        """
        return self.tripwire_thrown

    def get_clean_response(self) -> str:
        """Returns the clean-safe response.

        Returns:
            str: The clean response.
        """
        return self.response
