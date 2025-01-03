"""
Crawl for user sentiment on exmaples to create
"""

import time
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from src.model.news import News, NewsSource
from include.constants import SUBREDDIT_LIST, GITHUB_API_BASE
import requests
import os
import logging

from src.integrations.kbs.github_kb import GithubKnowledgeBase

GH_TRENDING_INTERVAL = timedelta(days=1)

class Crawl:
    """
    Crawl various kbs for user sentiment to create exmaples with
    """
    def __init__(self):
        self.news_cache: Dict[str, News] = {} # this should be the cached news within the timeframe. Stores some generic identifier for the news stories, id depends on the source type.
        
        # Github crawling stuff
        self.gh_token = os.getenv("GITHUB_TEST_TOKEN")
        self.github_headers = {
            "Authorization": f"Bearer {self.gh_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

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
            github_repos = self.crawl_github_trending()
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

    def crawl_github_trending(self) -> Dict[str, News]:
        """
        Crawl github trending for a list of repos and their content.
        Gets the top 15 repos by stars gained today.
        
        Returns:
            Dict[str, News]: Dictionary mapping repo names to News objects containing readme content
        """
        trending_news = {}
        GITHUB_URL = "https://github.com"

        try:
            url = f"{GITHUB_URL}/trending"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all repository articles
            for repo_article in soup.select('.Box article.Box-row')[:15]:
                # Extract repository info
                title = repo_article.select_one('.h3').text.strip()
                username, repo_name = [x.strip() for x in title.split('/')]
                relative_url = repo_article.select_one('.h3 a')['href']
                full_url = f"{GITHUB_URL}{relative_url}"

                # Get description
                description = repo_article.select_one('p.my-1')
                description = description.text.strip() if description else ''


                # Get readme content
                url = (
                    f"{GITHUB_API_BASE}/repos{relative_url}/contents/README.md"
                )
                readme_response = requests.get(
                    url,
                    headers=self.github_headers
                )

                if readme_response.status_code == 200:
                    repo_key = f"{username}/{repo_name}"
                    
                    body = readme_response.json()
                    content_response = requests.get(
                        body["download_url"], headers=self.github_headers
                    )
                    content_response.raise_for_status()

                    trending_news[repo_key] = News(
                        title=repo_key,
                        content=f"Description: {description}\nReadme: {str(content_response.content)}",
                        url=full_url,
                        source=NewsSource.GITHUB_TRENDING,
                        timestamp=datetime.now()
                    )

        except Exception as e:
            logging.error(f"Error crawling GitHub trending: {e}")
            
        return trending_news