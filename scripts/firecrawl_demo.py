import click
import anthropic
import subprocess
import os
from src.core.event.tool_actions.handle_newstream_action import NewStreamActionHandler
from src.example_creator.crawl import Crawl
from datetime import timedelta
from include.constants import EXAMPLE_CREATOR_TOOLS, NEWSCHECK_INTERVAL_HOURS

def get_handler() -> NewStreamActionHandler:
    """Initialize and return the NewStreamActionHandler"""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Initialize handler with required prompts and tools
    handler = NewStreamActionHandler(
        client=client,
        tools=EXAMPLE_CREATOR_TOOLS,
        tools_map={},  # Add tool implementations as needed
        model="claude-3.5-sonnet-latest",
        action_classifier_prompt="prompts/action_classifier.txt",
        execute_creation_prompt="prompts/example_creation.txt", 
        execute_modification_prompt="prompts/example_modification.txt"
    )
    return handler

def get_crawler() -> Crawl:
    """
    Get the crawler and crawl the news periodically. This should be fired off in a separate thread.

    Returns:
        Crawl: The crawler
    """
    crawler = Crawl()

    # Crawl the news periodically
    td = timedelta(hours=NEWSCHECK_INTERVAL_HOURS)
    crawler.crawl_news(td) # TODO: This should be fired off in a separate daemon thread.

    return crawler

@click.command()
@click.option('--action', type=click.Choice(['create', 'modify']), prompt='Select action',
              help='Create new example or modify existing one')
def main(action: str):
    """CLI interface for creating or modifying examples"""
    crawler = get_crawler()
    handler = get_handler()
    
    if action == 'create':
        click.echo("Creating new example...")
        # response = handler.handle_action([], is_creation=True)
        # click.echo(f"Creation response: {response}")
        
    else:  # modify
        click.echo("Modifying existing example...")
        # Get example ID or other identifier for modification
        example_id = click.prompt('Enter github repo example path to modify', type=str)
        # response = handler.handle_action([{"id": example_id}])
        # click.echo(f"Modification response: {response}")
