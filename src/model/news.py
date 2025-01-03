from pydantic import BaseModel
from enum import StrEnum

class NewsSource(StrEnum):
    REDDIT = "reddit"
    HACKER_NEWS = "hn" 
    GITHUB_TRENDING = "github_trending"

class News(BaseModel):
    title: str
    content: str
    url: str
    source: NewsSource