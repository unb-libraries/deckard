from langchain.chains import LLMChain
from logging import Logger
import json

from deckard.core import json_dumper, extract_first_json_block
from deckard.llm import fail_response

class QAResponder:
    """Processes QA sets to determine if a sets of standard QAs answers a query.

    Args:
        chain (LLMChain): The LLM chain to use.
        logger (Logger): The logger
    """
    def __init__(self, chain: LLMChain, logger: Logger) -> None:
        self.chain = chain
        self.logger = logger

    def query_responder(self, query, qa_data) -> tuple:
        """ Determines if a question is answered from a set of question-responses.

        Args:
            query (str): The query to check.
            qa_data (list[dict]): A list of dictionaries with question-response pairs. The dictionary should contain the keys "question", 
              "response", and a list of dicts with "text" and "url" for links.

        Returns:
            tuple (bool, string, list): If the question was answered by QA, the best-matching response, and the links.
        """
        has_response = False
        if qa_data is None or len(qa_data) == 0:
            self.logger.info("No data provided for QA responses")
            return has_response, fail_response(), []

        self.logger.info("Checking QA responses for query: %s", query)
        chain_response = self.chain.invoke(
            {
                "user_question": query,
                "qa_data": json_dumper(qa_data, pretty=True)
            }
        )

        self.response = chain_response

        self.logger.info("QA response: %s", chain_response)
        if isinstance(chain_response, str):
            first_json_block = extract_first_json_block(chain_response, "QA response", self.logger)
            if first_json_block is None:
                self.logger.error("Failed to extract JSON from response")
                return has_response, fail_response(), []
            self.logger.info("Decoded JSON response: %s", first_json_block)
            if "match" in first_json_block:
                has_response = first_json_block["match"]
                if has_response:
                    self.logger.info("Matched response: %s", first_json_block)
                    links = first_json_block.get("links", [])
                    self.logger.info("Links: %s", links)
                    return has_response, first_json_block.get("response", ""), links
            else:
                self.logger.error("Invalid response format: %s", chain_response)
                return has_response, fail_response(), []
        else:
            self.logger.error("Invalid response type: %s", type(chain_response))
        return has_response, fail_response(), []

def qa_response_prompt() -> str:
    """Returns the prompt that instructs the LLM to determine if a .

    Returns:
        str: The prompt.
    """
    return """<|start_header_id|>system<|end_header_id|>
You are a strict AI evaluator. Your ONLY job is to determine whether a user question is directly answered by a list of provided standardized question-response entries. You MUST IGNORE all external knowledge and MUST NOT attempt to generate responses or explanations based on training data.

Your output MUST follow this rule:
- If the question matches one of the entries questions exactly or with a clearly equivalent question meaning, respond with:
```json
{{
  "match": true,
  "response": "The answer from the matched entry.",
  "links": [
    {{
        "text": "Link1 Text",
        "url": "https://..."
    }},
    {{
        "text": "Link2 Text",
        "url": "https://..."
    }}
  ]
}}
```

- If there is any uncertainty, ambiguity, or the user question is NOT answered in the entries, you MUST respond ONLY with:
```json
{{ "match": false }}
```

DO NOT:
- Use prior knowledge.
- Invent answers or links.
- Say anything outside of the specified JSON structure.
- Attempt to answer unknown questions — you must treat anything not clearly matched as `{{ "match": false }}`.

<|start_header_id|>user<|end_header_id|>
Here is the user's question:
---
{user_question}
---

Here is the list of standardized question-answer entries:

```json
{qa_data}
```

Remember: ONLY answer if you are completely confident the user's question is answered by an entry. If not, respond with `{{ "match": false }}` and nothing else.
<|start_header_id|>assistant<|end_header_id|>
"""
