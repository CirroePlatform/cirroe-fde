from pydantic import BaseModel
from enum import StrEnum
from typing import List
from e2b.sandbox.commands.command_handle import CommandResult


class CodePageType(StrEnum):
    CODE = "code"
    DIRECTORY = "directory"


class CodePage(BaseModel):
    primary_key: str
    content: str
    org_id: str
    page_type: CodePageType
    sha: str


class ExecutionResult(BaseModel):
    build_success: bool
    execution_success: bool
    command_result: CommandResult
