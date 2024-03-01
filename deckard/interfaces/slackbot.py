import json
import os
import requests
import shlex

from deckard.core import get_rag_pipeline
from deckard.core import get_logger
from deckard.core.responses import error_response
from deckard.interfaces.api import api_server_up
from deckard.interfaces.api import get_api_uri
from logging import Logger
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

CMD_STRING = 'slackbot:start'

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
def query_llm(ack, respond, command):
    ack()
    command_data = shlex.split(command['text'])

    log.info(f"Received command: {shlex.split(command['text'])}")

    if not len(command_data) == 2:
        log.info(f"Invalid command: {command['text']}")
        respond(get_usage_display())
        return

    if get_rag_pipeline(command_data[0]) is None:
        log.info(f"Invalid pipeline: {command_data[0]}")
        respond(get_usage_display())
        return

    if command_data[1] == "":
        log.info(f"Empty query: {command_data[1]}")
        respond(get_usage_display())
        return

    if not api_server_up():
        log.error("Query API server cannot be reached.")
        respond(error_response())
        return

    uri = get_api_uri('/query')
    log.info(f"Querying {uri}...")
    r = requests.post(
        uri,
        json={
            "endpoint": command_data[0],
            "query": command_data[1],
            "client": "slack"
        }
    )
    rj = json.loads(r.text)
    respond(wrap_markdown_formatter(rj['response']))

def wrap_markdown_formatter(text: str) -> str:
    return '```' + text + '```'

def start() -> None:
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
