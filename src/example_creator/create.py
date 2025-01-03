"""
Create examples from user sentiment
"""

from core.event.tool_actions.handle_newstream_action import NewStreamActionHandler
from include.constants import (
    EXAMPLE_CREATOR_TOOLS,
    ACTION_CLASSIFIER,
    EXECUTE_CREATION,
    EXECUTE_MODIFICATION,
    MODEL_HEAVY,
)
from datetime import datetime, timedelta
from .crawl import Crawl
import anthropic
import logger
import time

NEWSCHECK_INTERVAL = 3  # In hours


class ExampleCreator:
    """
    create the physical examples from user sentiment, and open PRs
    """

    def __init__(self):
        self.crawler = Crawl()

        # 1. construct tools map for example creation.
        self.tools_map = {"": ""}

    def main(self):
        """
        Main loop to create a new example or edit an existing ones.
        """
        client = anthropic.Anthropic()

        action_handler = NewStreamActionHandler(
            client=client,
            tools=EXAMPLE_CREATOR_TOOLS,
            tools_map=self.tools_map,
            model=MODEL_HEAVY,
            action_classifier_prompt=ACTION_CLASSIFIER,
            execute_creation_prompt=EXECUTE_CREATION,
            execute_modification_prompt=EXECUTE_MODIFICATION,
        )

        while True:
            # 1. Call the news crawler over the current time - x seconds
            news_sources = self.crawler.crawl_news(
                datetime.now() - timedelta(hours=NEWSCHECK_INTERVAL)
            )

            # 2. Feed in the news sources to the action classifier, along with the search tools
            response = action_handler.handle_action(news_sources, 10)
            logger.info(response)

            # thread sleep for x seconds
            time.sleep(NEWSCHECK_INTERVAL * 60 * 60)
