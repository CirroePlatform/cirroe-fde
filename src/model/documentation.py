from pydantic import BaseModel

class DocumentationPage(BaseModel):
    url: str
    content: str
