from pydantic import BaseModel

class NewsSource(BaseModel):
    name: str

class News(BaseModel):
    title: str
    content: str
    url: str
    source: NewsSource