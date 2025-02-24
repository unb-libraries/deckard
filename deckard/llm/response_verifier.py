"""Provides the ResponseProcessor class."""
from langchain.chains import LLMChain
from logging import Logger
import json
import re

class ResponseVerifier:
    """Processes the response from the LLM.

    Args:
        response (str): The response to process.

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
            json_response = self.extract_first_json()
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

    def extract_first_json(self):
        try:
            json_pattern = r'\{.*?\}'
            matches = re.findall(json_pattern, self.response, re.DOTALL)
            
            if not matches:
                self.logger.error(f"Error parsing verification response: No JSON found")
                return None
            
            for match in matches:
                try:
                    parsed_json = json.loads(match)
                    return parsed_json
                except json.JSONDecodeError as je:
                    self.logger.error(f"Error parsing JSON: {je}")
                    continue 

            self.logger.error(f"Error parsing verification response: No valid JSON found")
            return None

        except Exception as e:
            self.logger.error(f"Error: {e}")
            return None

