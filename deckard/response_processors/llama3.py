from logging import Logger

class Llama3ResponseProcessor:
    """Provides a class that alters responses to remove undesired content. Should not be used to remove offensive content. See the 'malicious' chain.

    Args:
        log (Logger): The logger.

    Attributes:
        log (Logger): The logger.
        query (str): The query.
    """
    def __init__(self, response, log: Logger) -> None:
        self.log = log
        self.response = response

    def get_processed_response(self) -> str:
        """Returns the response after processing.

        Returns:
            str: The response.
        """
        # Strip nonsense like "Based on the provided context,"
        processed_response = self.response
        obtuse_prefixes = [
            'Based on the provided context,'
        ]
        for prefix in obtuse_prefixes:
            processed_response = processed_response.replace(prefix, '').strip()

        # Check if the response contains multiple lines, and the first words of the line start with prefixes
        obtuse_line_beginnings = [
            'The provided context'
        ]
        response_modified = False
        response_lines = processed_response.split('\n')
        for i, line in enumerate(response_lines):
            # Skip the first line
            if i == 0:
                continue
            for prefix in obtuse_line_beginnings:
                if line.startswith(prefix):
                    response_modified = True
                    response_lines[i] = ''
        if response_modified:
            processed_response = '\n'.join(response_lines).strip()

        return processed_response

    def get_original_response(self) -> str:
        """Returns the original response.

        Returns:
            str: The original response.
        """
        return self.response
