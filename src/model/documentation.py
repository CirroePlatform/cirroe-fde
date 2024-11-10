from pydantic import BaseModel
from uuid import UUID


class DocumentationPage(BaseModel):
    primary_key: str  # This ends up being a cryptographic hash, so str is fine.
    url: str
    content: str
