"""
Crawl for user sentiment on exmaples to create
"""

from typing import List, Optional
from datetime import datetime
class Crawl:
    """
    Crawl various kbs for user sentiment to create exmaples with
    """

    def __init__(self):
        pass

    def crawl_issues(self, n: int = 10) -> List[str]:
        """
        Crawl for the top n problems users of the product are facing
        """
        # 1. get the most recent messages from discord in all or specific channels.
        # 2. Cluster the messages into 
        return []

    def crawl_news(self, start_time: datetime, end_time: Optional[datetime] = None, n: int = 10) -> List[str]:
        """
        Crawl for the top n news articles about the product
        """
        if end_time is None:
            end_time = datetime.now()

        # 1. Crawl reddit for a list of posts and their content. Use a hardcoded list of subreddits.
        # 2. Crawl hacker news for a list of posts and their content.
        # 3. Crawl github trending for a list of the most popular repos. For each repo, get the readme.

        return []

# Potential news sources
# https://techurls.com/. no API, need to scrape
# Manually do reddit and hacker news.

# TOOLS
# 1. news crawler to get the top n news descriptions in the AI/tech/LLMs space.
# 2. github search to search over firecrawl, but also to search over other github repos for code that can help build examples.
# 3. example getter to get examples of other firecrawl examples.
# 4. pr opener
# 5. exa api for everything else.
