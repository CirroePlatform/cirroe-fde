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

# Requirements:
# Research & Discovery: Continuously monitor top platforms (e.g., X/Twitter, GitHub Trending, various tech news aggregators)
# to identify the latest frameworks, libraries, AI models, and development patterns most relevant to Firecrawl.
#  - Focus on just X/Github/reddit for now.
# crawl.py

# Creative Example Creation:
# Build example apps showcasing unique use-cases with Firecrawl, integrating trending technologies and industry best practices.
# Focus on frameworks such as Next.js or Python-based stacks, ensuring that the examples are both innovative and educational.
#  - Create use cases based on discord/slack/git issues search + current events to see what issues devs are facing using firecrawl, and what
#    is popping in the industry right now. Focus on single page code first.
# create.py
 
# Testing & Quality Assurance:
# Rigorously test all example applications to ensure correctness, performance, security, and maintainability.
# Validate compatibility with the latest Firecrawl features and ensure that examples run smoothly in various environments.
#  - use E2B for sandbox testing. If it's compiling and running in a python sandbox with the latest firecrawl version, good to go.
# sandbox.py

# Documentation & Guides:
# Write clear, concise documentation and comments to guide developers through setup, usage, and customization of the sample apps.
# Include notes on the trending technologies integrated, explaining the reasoning and potential benefits.
#  - Include the above in the prompt when creating the example page.

# Version Control & PRs:
# Regularly open pull requests (PRs) to update the firecrawl/examples folder with new or improved sample applications.
#  - Setup cron job on railway to continuously search for new events + open PRs. Frequency should be every time some new news is created,
#   or if the crawler deems some new issue to be super popular and there's developer demand.
# create.py
# main.py