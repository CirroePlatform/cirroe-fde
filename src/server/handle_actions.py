from pydantic import BaseModel
from uuid import UUID
from typing import Tuple

from src.storage.vector import VectorDB
from src.model.runbook import Runbook, UploadRunbookRequest
from src.model.issue import Issue, OpenIssueRequest

from src.core.runbook import RunBookExecutor


RUNBOOKS = {} # {rid: runbook}

vector_db = VectorDB()
rb_executor = RunBookExecutor()


class IssueUpdateRequest(BaseModel):
    issue: Issue
    new_comment: Tuple[UUID, str]

def handle_new_runbook(runbook_req: UploadRunbookRequest):
    """
    Called from the server endpoint, handles a new runbook request
    """
    if runbook_req.runbook.rid not in RUNBOOKS:
        vector_db.add_runbook(runbook_req.runbook)

def handle_new_issue(new_issue_request: OpenIssueRequest):
    """
    Handle a new inbound issue filed.
    """
    # top_k_similar_runbooks = self.db_client.get_top_k(issue.problem_description)
    top_k_similar_runbooks = []

    # 1. Find runbook for issue.
    runbook = rb_executor.get_runbook_for_issue(new_issue_request.issue, top_k_similar_runbooks)

    # 2. if runbook exists, call the runbook executor to run the book.
    response = rb_executor.run_book(runbook) # This will block at certain points via humanlayer

    # 3. If dne, alert some person with the correct background to handle the issue.
    if response is None:
        return "Couldn't run book"

    return response

def handle_issue_update(issue_update):
    """
    Handle an update to the issue from anyone.
    
    STRETCH
    """
    pass
