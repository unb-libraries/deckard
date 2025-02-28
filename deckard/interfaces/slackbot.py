"""Provides a simple one-shot Slackbot interface for Deckard."""
import json
import requests
import shlex

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from deckard.core import get_logger, get_rag_pipeline, available_rag_pipelines_message, get_slack_config
from deckard.interfaces.api import api_server_up
from deckard.llm.responses import error_response

DECKARD_CMD_STRING = 'slackbot:start'

config = get_slack_config()
log = get_logger()
app = App(
    token=config['slack_bot_token'],
    logger=log
)

@app.command("/query_llm")
def slack_events(ack: callable, respond: callable, command: str) -> None:
    """ Handles events from Slack.

    Args:
        ack (callable): The ack function.
        respond (callable): The respond function.
        command (str): The command to handle.
    """
    ack()
    command_data = shlex.split(command['text'])

    log.info("Received command: %s", shlex.split(command['text']))
    if not len(command_data) == 2:
        log.info("Invalid command: %s", command['text'])
        respond(get_user_usage_example())
        return

    if get_rag_pipeline(command_data[0]) is None:
        log.info("Invalid pipeline: %s", command_data[0])
        respond(get_user_usage_example())
        return

    if command_data[1] == "":
        log.info("Empty query: %s", command_data[1])
        respond(get_user_usage_example())
        return

    if not api_server_up():
        log.error("API server cannot be reached.")
        respond(error_response())
        return

    try:
        response = requests.post(
            'https://aigateway.lib.unb.ca/deckard/api/v1',
            json={
                'query': command_data[1],
                'client': 'deckard slackbot',
                'pipeline': command_data[0]
            },
            headers={
                'x-pub-key': config['api_pub_key'],
                'x-api-key': config['api_priv_key']
            }
        )
        response.raise_for_status()
        rj = response.json()

        text_response = rj.get('response')
        if text_response is None:
            log.error("No response found in API response")
            respond(error_response())
            return
        sources = rj.get('source_urls')
        if sources != None and sources != {}:
            try:
                if 'source_urls' in sources:
                    source_urls = sources['source_urls']
                    if source_urls == None or source_urls == []:
                        log.error("No source URLs found in API response")
                    else:
                        valid_urls = get_valid_urls(source_urls)
                        if valid_urls == None or valid_urls == []:
                            log.error("No valid URLs found in API response")
                        else:
                            text_response += f" [Sources: {", ".join(valid_urls)}]"
            except json.JSONDecodeError:
                log.error("Failed to decode source URLs")
        respond(text_response)
    except requests.RequestException as e:
        log.error("Request failed: %s", e)
        respond(error_response())

def wrap_markdown_formatter(text: str) -> str:
    """Wraps the text in markdown formatting.

    Args:
        text (str): The text to wrap.

    Returns:
        str: The wrapped text.
    """
    return '```' + text + '```'

def start() -> None:
    """Starts the Slackbot."""
    handler = SocketModeHandler(app, config['slack_app_token'])
    handler.start()

def get_user_usage_example() -> str:
    """Gets the usage message for the Slack User.

    Returns:
        str: The usage message.
    """
    return wrap_markdown_formatter(
        f"Usage: /query_llm <pipeline> <query>. {available_rag_pipelines_message()}"
    )

def get_valid_urls(urls: list) -> list:
    """Gets the valid URLs from a list of URLs.

    Args:
        urls (list): The list of URLs.

    Returns:
        list: The valid URLs.
    """
    valid_urls = []
    for url in urls:
        try:
            response = requests.get(url, allow_redirects=True)
            valid_urls.append(response.url)
        except requests.HTTPError as e:
            log.error(f"HTTP error: {e}")
        except requests.RequestException as e:
            log.error(f"Request error: {e}")
    return valid_urls
