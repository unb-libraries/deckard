from langchain.chains import LLMChain
from logging import Logger

from deckard.core import json_dumper
from deckard.llm import fail_response

class CompoundResponseSummarizer:
    """Processes response data to summarize multiple responses into a single paragraph.

    Args:
        chain (LLMChain): The LLM chain to use.
        logger (Logger): The logger
    """
    def __init__(self, chain: LLMChain, logger: Logger) -> None:
        self.chain = chain
        self.logger = logger

    def summarize(self, data) -> tuple:
        """ Summarizes multiple responses into a single paragraph.

        Args:
            data (list[dict]): A list of dictionaries with keys 'query', 'response', and 'is_answer'.

        Returns:
            tuple (str, bool, bool): The response/summarization was run/at least one of the queries was answered.
        """
        if not data:
            self.logger.info("No data provided for summarization")
            return fail_response(), False, False
        
        has_response = False
        for item in data:
            if item['is_answer']:
                has_response = True
                break

        if not has_response:
            self.logger.info("No responses answered their queries")
            return fail_response(), False, False

        # If only one response, return it. No need to summarize.
        if len(data) == 1:
            self.logger.info("Only one response provided, not summarizing")
            return data[0]['response'], False, True

        chain_data = []
        for item in data:
            if item['is_answer']:
                cur_response = item['response']
            else:
                cur_response = ''
            chain_data.append(
                {
                    "query": item['query'],
                    "response": cur_response,
                    "is_response": item['is_answer']
                }
            );

        self.logger.info("Summarizing responses")
        chain_response = self.chain.invoke(
            {
                "json_data": json_dumper(chain_data)
            }
        )

        self.response = chain_response
        return chain_response, True, True

def summarize_response_prompt() -> str:
    """Returns the prompt that instructs the LLM to summarize a single response from multiple queries.

    Returns:
        str: The prompt.
    """
    return """
<|start_header_id|>system<|end_header_id|> 
You are an expert assistant that consolidates multiple queries and responses into a single, well-structured response paragraph.<|eot_id|>

<|start_header_id|>user<|end_header_id|> 
Here is a list of queries, responses, and flags indicating whether the response actually addresses the query. Your task is to:

1. Combine all **valid responses** into a single concise natural, coherent paragraph, removing redundant information.
2. If any query has is_response = false, ignore the query when constructing your response.
3. If any query has is_response = false, conclude your response with a statement "I could not find any other information."
4. Ensure the final response is well-structured, readable, and maintains logical flow.

## Input Data:
```
{json_data}
```

## Output Format
Return a **single concise statement** that summarizes all provided responses.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
