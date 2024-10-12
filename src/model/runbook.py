from pydantic import BaseModel
from typing import List, Tuple, Optional
from uuid import UUID

class Step(BaseModel):
    """
    A single step to execute in a runbook.
    Single link in the linked list.
    """

    sid: UUID
    description: str
    allowed_cmds: List[str]
    next: Optional[UUID] = None


class Runbook(BaseModel):
    """
    Model representing a runbook defined by the user
    
    ALERT this is different from the vector db schema, in the vector db
    we just store a list of uuids for the steps instead of the steps. The actual
    steps are in the supabase table called 'steps'
    """

    rid: UUID
    description: str
    steps: List[Step]
    vector: Optional[List[float]] = None


class UploadRunbookRequest(BaseModel):
    upload_user_id: UUID
    runbook: Runbook
