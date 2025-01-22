"""Provides a command to query RAG pipelines."""
import sys

from logging import Logger
import requests

from deckard.core.config import get_client_keypair, get_client_uri, get_client_user_agent, get_client_timeout
from deckard.core.jsoncore import json_dumper
from deckard.core.config import get_api_host, get_api_port

def query_api(query_data: dict, log: Logger) -> dict:
    uri = get_client_uri()
    log.info("Querying %s...", uri)

    keypair = get_client_keypair()

    headers = {
        "x-pub-key": keypair[0],
        "x-api-key": keypair[1],
    }

    query_data['user-agent'] = get_client_user_agent()

    r = requests.post(
        uri,
        json=query_data,
        headers=headers,
        timeout=get_client_timeout()
    )

    if r.status_code != 200:
        log.error("Query responds with failure:")
        log.error(r.text)
        sys.exit(1)

    print(
        json_dumper(r.json())
    )

def legacy_post_query_to_api(
        query: str,
        endpoint: str,
        client: str,
        log: Logger,
        context: str='',
        pipeline: str=''
    ) -> requests.Response:
    """Posts a query to the API server.

    Args:
        query (str): The query to post.
        endpoint (str): The endpoint to query.
        client (str): The client name to assert.
        log (Logger): The logger to use.
        context (str, optional): The context to use. Defaults to ''.
        pipeline (str, optional): The RAG pipeline to use. Defaults to ''.

    Returns:
        requests.Response: The response from the API server.
    """
    uri = legacy_get_api_uri(endpoint)
    log.info("Querying %s...", uri)

    json_query = {
        "context": context,
        "client": client,
        "pipeline": pipeline,
        "query": query
    }
    
    log.info("JSON query: %s", json_query)

    return requests.post(
        uri,
        json={
            "context": context,
            "client": client,
            "pipeline": pipeline,
            "query": query
        },
        timeout=300
    )

def legacy_get_api_uri(endpoint: str='/query/raw') -> str:
    """Gets the URI for the API server.

    Args:
        endpoint (str, optional): The endpoint to use. Defaults to '/query/raw'.

    Returns:
        str: The URI for the API server.
    """
    return 'http://' + get_api_host() + ':' + str(get_api_port()) + endpoint