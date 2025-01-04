import logging
import traceback
import praw
from datetime import datetime, timedelta
from typing import Any, List, Optional, Tuple
from uuid import UUID
import os

from src.integrations.kbs.base_kb import BaseKnowledgeBase, KnowledgeBaseResponse


class RedditKnowledgeBase(BaseKnowledgeBase):
    """
    Knowledge base integration for Reddit data.
    Provides interface for indexing and querying Reddit posts.
    """

    def __init__(self, org_id: UUID):
        """
        Initialize Reddit knowledge base

        Args:
            org_id: Organization ID to scope the knowledge base
        """
        super().__init__(org_id)

        # Initialize Reddit API client
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="CirroeBot/1.0 by Puzzleheaded-Boot986",
        )

    async def index(self, data: Any) -> bool:
        """
        Index Reddit post data into the knowledge base

        Args:
            data: Reddit post data to be indexed

        Returns:
            bool: True if indexing was successful
        """
        try:
            # TODO: Implement indexing logic
            return True
        except Exception as e:
            logging.error(f"Failed to index Reddit data: {str(e)}")
            return False

    def query(
        self, query: str, limit: int = 5, tb: Optional[str] = None, **kwargs
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
        Query the Reddit knowledge base

        Args:
            query: Natural language query string
            limit: Maximum number of results to return
            tb: Optional traceback string

        Returns:
            Tuple of (List of KnowledgeBaseResponse objects, Answer string)
        """
        try:
            # TODO: Implement query logic
            return [], ""
        except Exception as e:
            logging.error(f"Failed to query Reddit knowledge base: {str(e)}")
            return [], ""

    def get_images_from_post(self, post: praw.models.Submission) -> List[str]:
        """
        Get images from a post
        """
        # Check if the post has a direct image link
        if post.url.endswith((".jpg", ".png", ".gif", ".jpeg", ".webp")):
            return [post.url]

        # Check if the post is a gallery post (Reddit-hosted image)
        images = []
        if hasattr(post, "gallery_data") and post.is_gallery:
            for item in post.gallery_data["items"]:
                media_id = item["media_id"]
                img_url = f"https://i.redd.it/{media_id}.jpg"
                images.append(img_url)

        # Check if the post is a media post (Reddit-hosted image)
        if hasattr(post, "is_reddit_media_domain") and post.is_reddit_media_domain:
            if (
                hasattr(post, "is_video") and not post.is_video
            ):  # ignoring videos for now.
                images.append(post.url)

        return images

    def get_top_posts(
        self,
        subreddit_name: str,
        limit: int = 10,
        time_interval: timedelta = timedelta(days=1),
    ) -> List[dict]:
        """
        Get top posts from a subreddit within a time interval

        Args:
            subreddit_name: Name of subreddit to query
            limit: Maximum number of posts to return
            time_interval: Time interval to look back from now

        Returns:
            List of dictionaries containing post data
        """
        try:
            # Calculate start time
            start_time = datetime.now() - time_interval

            # Get subreddit instance
            subreddit = self.reddit.subreddit(subreddit_name)

            # Get top posts
            posts = []
            for post in subreddit.top(time_filter="day"):
                post_time = datetime.fromtimestamp(post.created_utc)
                images = self.get_images_from_post(post)

                if post_time >= start_time:
                    posts.append(
                        {
                            "id": post.id,
                            "title": post.title,
                            "content": post.selftext,
                            "url": post.url,
                            "score": post.score,
                            "created_utc": post.created_utc,
                            "num_comments": post.num_comments,
                            "author": str(post.author),
                            "images": images,
                        }
                    )

            return posts

        except Exception as e:
            traceback.print_exc()
            logging.error(f"Failed to get top posts from {subreddit_name}: {str(e)}")
            return []
