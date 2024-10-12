from pydantic import BaseModel
from typing import List, Tuple
from uuid import UUID

class Issue(BaseModel):
    """
    Model for a customer issue, could be issue, slack thread, etc.
    """

    tid: UUID
    problem_description: str
    comments: List[Tuple[str, str]] # a list of (requestor_name, comment) objects

class OpenIssueRequest(BaseModel):
    requestor: str
    issue: Issue
