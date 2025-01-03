from pydantic import BaseModel
from enum import StrEnum
from datetime import datetime
from typing import List 


class NewsSource(StrEnum):
    REDDIT = "reddit"
    HACKER_NEWS = "hn"
    GITHUB_TRENDING = "github_trending"


class News(BaseModel):
    title: str
    content: str
    url: str
    source: NewsSource

class RedditNews(News):    
    images: List[str]
    score: int
    created_utc: datetime
    num_comments: int
    author: str
