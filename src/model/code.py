from pydantic import BaseModel
from enum import StrEnum
from typing import List

class CodePageType(StrEnum):
    CODE = "code"
    DIRECTORY = "directory"

class CodePage(BaseModel):
    primary_key: str
    content: str
    vector: List[float]
    org_id: str
    page_type: CodePageType
