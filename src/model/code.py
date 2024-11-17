from pydantic import BaseModel
from enum import StrEnum
from typing import List, Optional


class CodePageType(StrEnum):
    CODE = "code"
    DIRECTORY = "directory"


class CodePage(BaseModel):
    primary_key: str
    org_id: str
    page_type: CodePageType
    name: str
    vector: List[float]

    summary: Optional[str] = None
    code_content: Optional[str] = None
