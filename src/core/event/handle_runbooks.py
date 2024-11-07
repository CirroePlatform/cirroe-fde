from pydantic import BaseModel
from uuid import UUID
from typing import Tuple
from dotenv import load_dotenv

from src.storage.vector import VectorDB
from src.model.runbook import UploadRunbookRequest
from src.model.issue import Issue

load_dotenv()

RUNBOOKS = {}  # {rid: runbook}


class IssueUpdateRequest(BaseModel):
    issue: Issue
    new_comment: Tuple[UUID, str]


def handle_new_runbook(runbook_req: UploadRunbookRequest):
    """
    Called from the server endpoint, handles a new runbook request
    """
    vector_db = VectorDB(runbook_req.user_id)
    if runbook_req.runbook.rid not in RUNBOOKS:
        vector_db.add_runbook(runbook_req.runbook)
