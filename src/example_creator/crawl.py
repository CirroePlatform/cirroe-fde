"""
Crawl for user sentiment on exmaples to create
"""

import time
from typing import List, Dict
from datetime import datetime, timedelta
from src.model.news import News, NewsSource
from include.constants import SUBREDDIT_LIST
import requests
import logging


class Crawl:
    """
    Crawl various kbs for user sentiment to create exmaples with
    """
    def __init__(self):
        self.news_cache: Dict[str, News] = {} # this should be the cached news within the timeframe. Stores some generic identifier for the news stories, id depends on the source type.

    def crawl_issues(self, n: int = 10) -> List[str]:
        """
        Crawl for the top n problems users of the product are facing
        """
        # 1. get the most recent messages from discord in all or specific channels.
        # 2. Cluster the messages into 
        return []

    def crawl_news(self, interval: timedelta):
        """
        Crawl for the top n news articles about the product. Constantly updates the news cache.

        Eviction is time based. If we have news that is older than the interval, we remove it. If we also 
        exceed the max cache size, we remove the oldest news.
        """
        while True:
            end_time = datetime.now()
            start_time = end_time - interval

            # 1. Crawl reddit for a list of posts and their content. Use a hardcoded list of subreddits.
            reddit_news = self.crawl_reddit(SUBREDDIT_LIST)
            self.news_cache.update(reddit_news)

            # 2. Crawl hacker news for a list of posts and their content.
            hn_posts = self.crawl_hacker_news(start_time, end_time)
            self.news_cache.update(hn_posts)

            # 3. Crawl github trending for a list of the most popular repos. For each repo, get the readme.
            github_repos = self.crawl_github_trending(start_time, end_time)
            self.news_cache.update(github_repos)

            # 4. Sleep for the interval - time taken to crawl.
            time.sleep(interval.total_seconds())

    def crawl_reddit(self, subreddit_list: List[str]) -> Dict[str, News]:
        """
        Crawl reddit for a list of posts and their content.
        """
        return {}

    def crawl_hacker_news(self, start_time: datetime, end_time: datetime) -> Dict[str, News]:
        """
        Crawl hacker news for a list of posts and their content.
        """
        return {}

    def crawl_github_trending(self, start_time: datetime, end_time: datetime) -> Dict[str, News]:
        """
        Crawl github trending for a list of repos and their content.
        
        Returns:
            Dict[str, News]: Dictionary mapping repo names to News objects containing readme content
        """
        trending_news = {}

        try:
            # Get trending repos from GitHub API
            response = requests.get(
                "https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc"
            )
            response.raise_for_status()
            
            repos = response.json()["items"]
            
            # Process each trending repo
            for repo in repos:
                repo_name = f"{repo['owner']['login']}/{repo['name']}"
                
                # Get readme content
                readme_response = requests.get(
                    f"https://api.github.com/repos/{repo_name}/readme",
                    headers={"Accept": "application/vnd.github.raw"}
                )
                
                if readme_response.status_code == 200:
                    trending_news[repo_name] = News(
                        title=repo_name,
                        content=readme_response.text,
                        url=repo["html_url"],
                        source=NewsSource.GITHUB_TRENDING,
                        timestamp=datetime.strptime(repo["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                    )
                    
        except Exception as e:
            logging.error(f"Error crawling GitHub trending: {e}")
            
        return trending_news

# TOOLS
# 1. news crawler to get the top n news descriptions in the AI/tech/LLMs space.
# 2. github search to search over firecrawl, but also to search over other github repos for code that can help build examples.
# 3. example getter to get examples of other firecrawl examples.
# 4. pr opener
# 5. exa api for everything else.
