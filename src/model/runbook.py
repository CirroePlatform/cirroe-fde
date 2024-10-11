from pydantic import BaseModel
from typing import List, Tuple
from uuid import UUID

class Step(BaseModel):
    """
    A single step to execute in a runbook. 
    Single link in the linked list.
    """
    sid: UUID
    description: str
    allowed_cmds: List[str]
    next_steps: Tuple[str, UUID] # A tuple of the next step condition, step to go to.

class Runbook(BaseModel):
    """
    Model representing a runbook defined by the user
    """
    rid: UUID
    description: str
    first_step_id: UUID
