from pydantic import BaseModel
from typing import List
from uuid import UUID


class Comment(BaseModel):
    """
    Model for a comment on an issue
    """

    requestor_id: int
    content: str
    ts: int  # might need to change this to time class


class Issue(BaseModel):
    """
    Model for a customer issue, could be issue, slack thread, etc.
    """

    tid: int
    problem_description: str
    comments: List[Comment]


class OpenIssueRequest(BaseModel):
    requestor: UUID
    issue: Issue
