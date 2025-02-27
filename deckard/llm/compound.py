import json
import re

from langchain.chains import LLMChain
from logging import Logger

from deckard.core import extract_first_json_block

class CompoundClassifier:
    """Processes the user query to determine if it is a compound query, returning the sub-queries.

    Args:
        query (str): The query to process.

    Attributes:
        query (dict): The query, broken down into sub-queries.
    """
    def __init__(self, query: str, chain: LLMChain, logger: Logger) -> None:
        self.query = query
        self.chain = chain
        self.logger = logger

    def explode_query(self) -> tuple:
        """ Breaks the query into sub-queries

        Returns:

            tuple (queries (dict), reason): The query, broken down into sub-queries, and the reason for the result.
        """
        chain_response = self.chain.invoke(
            {
                "query": self.query
            }
        )
        self.response = chain_response

        try:
            json_response = extract_first_json_block(self.response, "SubQuery Extraction", self.logger)
            if json_response is None:
                reason = "Error parsing malicious response: no JSON found in extracted text"
                self.logger.error(reason)
                return json.loads("{}"), self.response, reason
            return json_response, self.response, "Successful"
        except Exception as e:
            reason = f"Error parsing malicious response: {e}"
            self.logger.error(reason)
            return json.loads("{}"), self.response, reason


def explode_query_prompt() -> str:
    """Returns the prompt that instructs the LLM to break down a query into sub-queries.

    Returns:
        str: The prompt.
    """
    return """You are an AI assistant that extracts distinct queries from user input. Given some user input, determine if it contains multiple distinct queries. If it does, extract each distinct query and return them in a structured JSON format.

## Task:
- Identify if the query contains more than one query.
- If so, extract each distinct query as a separate entry.
- Format the output as a JSON object with an array of queries.
- Each query should be labeled with an index and its corresponding extracted query.
- Maintain the original wording as much as possible.
- If the query contains only one query, return it as a single entry in the same format.

## Example Output Format:
Example Input 1:
"What is the capital of France, and who is the current president?"

Example Output 1:
{{
  "is_compound": true,
  "queries": {{
    "1": "What is the capital of France?",
    "2": "Who is the current president?"
  }}
}}

Example Input 2:
"How does photosynthesis work?"

Example Output 2:
{{
  "is_compound": false,
  "queries": {{
    "1": "How does photosynthesis work?"
  }}
}}

## Inputs:
<|start_header_id|>User Input:<|end_header_id|>
{query}

## Output:
Respond **only** with the JSON object in the specified format. Do not include any additional text.
"""
