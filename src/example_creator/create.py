"""
Create examples from user sentiment
"""

from .crawl import Crawl
from include.constants import EXAMPLE_CREATOR_TOOLS

class ExampleCreator:
    """
    create the physical examples from user sentiment, and open PRs
    """

    def __init__(self):
        self.crawler = Crawl()

        # 1. construct tools map for example creation.
        self.tools_map = {
            "crawl": self.crawler.crawl,
        }

    def main(self):
        """
        Main loop to create a new example or edit an existing ones.
        """

        # 2. tools map should have a the crawler to get the user sentiment about the top n problems they're facing.
        
        # 3. trigger main tools calling loop
        
        # 4. given the main output, craft an example string in markdown.
        
        # 5. open a PR with the example string.
        
        pass
