import click
import anthropic
import subprocess
import os
from src.core.event.tool_actions.handle_newstream_action import NewStreamActionHandler
from src.example_creator.crawl import Crawl
from src.example_creator.sandbox import Sandbox
from datetime import timedelta
from include.constants import (
    EXAMPLE_CREATOR_CLASSIFIER_TOOLS,
    NEWSCHECK_INTERVAL_HOURS,
    FIRECRAWL_ORG_ID,
)
from src.core.tools import SearchTools


def get_handler() -> NewStreamActionHandler:
    """Initialize and return the NewStreamActionHandler"""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    search_tools = SearchTools(requestor_id=FIRECRAWL_ORG_ID)
    sandbox = Sandbox()

    tools_map = {
        "execute_search": search_tools.execute_search,
        "get_existing_examples": None,
        "get_example_contents": None,
        "search_web": search_tools.web_kb.query,
        "run_code_e2b": sandbox.run_code_e2b,
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
