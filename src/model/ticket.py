from pydantic import BaseModel
from typing import List

class Comment(BaseModel):
    """
    Model for a comment on an issue
    """
    requestor_id: int
    content: str
    ts: int # might need to change this to time class

class Issue(BaseModel):
    """
    Model for a customer issue, could be ticket, slack thread, etc.
    """
    tid: int
    problem_description: str
    comments: List[Comment]

class IssueType(BaseModel):
    """
    Issue type. used for classification purposes.
    """
    name: str
