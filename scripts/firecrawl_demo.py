from src.core.event.tool_actions.handle_newstream_action import NewStreamActionHandler
from src.example_creator.sandbox import Sandbox
from include.utils import get_latest_version
from src.example_creator.crawl import Crawl
from src.core.tools import SearchTools
from datetime import timedelta
from typing import List, Tuple
import anthropic
import requests
import logging
import click
import os

from include.constants import (
    EXAMPLE_CREATOR_CLASSIFIER_TOOLS,
    NEWSCHECK_INTERVAL_HOURS,
    FIRECRAWL_ORG_ID,
    GITHUB_API_BASE,
)


def get_firecrawl_existing_examples() -> Tuple[str, List[str]]:
    """Get list of example filenames from the firecrawl/examples directory on GitHub

    Returns:
        List[str]: List of example filenames from the examples directory
    """
    search_tools = SearchTools(requestor_id=FIRECRAWL_ORG_ID)
    example_files = []

    try:
        # Get contents of examples directory
        url = f"{GITHUB_API_BASE}/repos/mendableai/firecrawl/contents/examples"
        response = requests.get(url, headers=search_tools.github.github_headers)
        response.raise_for_status()

        # Extract filenames from response
        contents = response.json()
        for item in contents:
            if item["type"] == "dir":
                example_files.append(item["name"])

    except Exception as e:
        logging.error(f"Failed to fetch example files: {str(e)}")

    return ", ".join(example_files), example_files


def get_handler() -> NewStreamActionHandler:
    """Initialize and return the NewStreamActionHandler"""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    search_tools = SearchTools(requestor_id=FIRECRAWL_ORG_ID)
    sandbox = Sandbox()

    tools_map = {
        "execute_search": search_tools.execute_search,
        "get_existing_examples": get_firecrawl_existing_examples,
        "get_example_contents": search_tools.github.fetch_contents,
        "search_web": search_tools.web_kb.query,
        "run_code_e2b": sandbox.run_code_e2b,
        "get_latest_version": get_latest_version,
    }

    # Initialize handler with required prompts and tools
    handler = NewStreamActionHandler(
        client=client,
        tools=EXAMPLE_CREATOR_CLASSIFIER_TOOLS,
        tools_map=tools_map,
        model="claude-3-5-sonnet-20241022",
        action_classifier_prompt="include/prompts/example_builder/action_classifier.txt",
        execute_creation_prompt="include/prompts/example_builder/execute_creation.txt",
        execute_modification_prompt="include/prompts/example_builder/execute_modification.txt",
        product_name="firecrawl",
        org_name="mendableai",
        org_id=FIRECRAWL_ORG_ID,
    )

    return handler


def get_crawler(debug: bool = False) -> Crawl:
    """
    Get the crawler and crawl the news periodically. This should be fired off in a separate thread.

    Returns:
        Crawl: The crawler
    """
    crawler = Crawl()

    # Crawl the news periodically
    td = timedelta(hours=NEWSCHECK_INTERVAL_HOURS)
    crawler.crawl_news(
        td, debug=debug
    )  # TODO: This should be fired off in a separate daemon thread.

    return crawler


def main(action: str):
    """CLI interface for creating or modifying examples"""
    handler = get_handler()
    crawler = get_crawler(debug=True)

    if action == "create":
        click.echo("Creating new example...")
        response = handler.handle_action(crawler.news_cache)
        click.echo(f"Creation response: {response}")
    elif action == "thread":
        click.echo("Beginning Cirroe daemon...")
        # TODO: have the agent decide what to do.
