from pydantic import BaseModel
from uuid import UUID
from typing import Tuple, List
import anthropic
from dotenv import load_dotenv

from src.storage.vector import VectorDB, DEBUG_ISSUE_TOOLS
from src.model.runbook import UploadRunbookRequest
from src.model.issue import Issue, OpenIssueRequest

from src.core.executor import RunBookExecutor
from src.integrations.merge import client as merge_client, CommentRequest

load_dotenv()

RUNBOOKS = {}  # {rid: runbook}

rb_executor = RunBookExecutor()
vector_db = VectorDB()


class IssueUpdateRequest(BaseModel):
    issue: Issue
    new_comment: Tuple[UUID, str]


def handle_new_runbook(runbook_req: UploadRunbookRequest):
    """
    Called from the server endpoint, handles a new runbook request
    """
    if runbook_req.runbook.rid not in RUNBOOKS:
        vector_db.add_runbook(runbook_req.runbook)


def handle_issue_update(issue_update):
    """
    Handle an update to the issue from anyone.

    STRETCH
    """
    pass
