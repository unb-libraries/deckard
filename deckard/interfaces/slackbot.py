"""Provides a Slackbot interface for Deckard."""
import json
import os
import shlex

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from deckard.core import get_logger, get_rag_pipeline, available_rag_pipelines_message
from deckard.interfaces.api import api_server_up
from deckard.llm.responses import error_response
from deckard.interfaces.client import legacy_post_query_to_api

DECKARD_CMD_STRING = 'slackbot:start'

# This socketmode app can be translated to a listener endpoint for slack.
# It listens for messages and responds to them.
SLACK_BOT_TOKEN=os.environ['SLACK_BOT_TOKEN']
SLACK_APP_TOKEN=os.environ['SLACK_APP_TOKEN']

log = get_logger()
app = App(
    token=SLACK_BOT_TOKEN,
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

    r = legacy_post_query_to_api(
        command_data[1],
        '/query',
        'slackbot',
        log,
        pipeline=command_data[0]
    )
    rj = json.loads(r.text)
    respond(wrap_markdown_formatter(rj['response']))

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
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()

def get_user_usage_example() -> str:
    """Gets the usage message for the Slack User.

    Returns:
        str: The usage message.
    """
    return wrap_markdown_formatter(
        f"Usage: /query_llm <pipeline> <query>. {available_rag_pipelines_message()}"
    )
