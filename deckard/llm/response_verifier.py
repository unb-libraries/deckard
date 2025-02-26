import json
import re

from langchain.chains import LLMChain
from logging import Logger

from deckard.core import extract_first_json_block

class ResponseVerifier:
    """Processes the response from the LLM and determines if it addresses the query.

    Args:
        query (str): The query to process.
        response (str): The response to process.
        chain (LLMChain): The LLM chain to use.
        logger (Logger): The logger to use.

    Attributes:
        response (str): The response to process.
    """
    def __init__(self, query: str, response: str, chain: LLMChain, logger: Logger) -> None:
        self.response = response
        self.query = query
        self.chain = chain
        self.logger = logger

    def response_answers_question(self) -> tuple:
        """Returns if the response does answer the question along with the reason.

        Returns:
            tuple: (bool, str) indicating if the response answers the question and the reason.
        """
        chain_response = self.chain.invoke(
            {
                "query": self.query,
                "response": self.response
            }
        )
        self.response = chain_response
        self.logger.info(f"Verification Response: {self.response}")
        try:
            json_response = extract_first_json_block(self.response, "Verification Reponse", self.logger)
            if json_response is None:
                reason = "Error parsing verification response: no JSON found in extracted text"
                self.logger.error(reason)
                return False, reason, json.loads("{}")
            if 'is_answer' in json_response:
                return json_response['is_answer'], "Success", json_response
            else:
                reason = "Error parsing verification response: 'is_answer' not found in eval"
                self.logger.error(reason)
                return False, reason, json.loads("{}")
        except Exception as e:
            reason = f"Error parsing verification response: {e}"
            self.logger.error(reason)
            return False, reason, json.loads("{}")

def response_addresses_query_prompt() -> str:
    """Returns the prompt that determines if a query addresses a question with useful information.

    Returns:
        str: The prompt.
    """

    return """
You are an AI assistant evaluating whether a given response directly answers the original question. If the response contains "there is no information about", consider the answer irrelevant.

## Task:
Return ONLY a structured JSON object evaluating whether the response is a direct and relevant answer.

## JSON Output Format:
```
{{
  "is_answer": <true/false>,
  "reason": "<brief explanation>"
}}
```

## Inputs:
<|start_header_id|>Question:<|end_header_id|>
{query}

<|start_header_id|>Response:<|end_header_id|>
{response}

## Output:
Respond **only** with the JSON object in the specified format. Do not include any additional text.
"""
