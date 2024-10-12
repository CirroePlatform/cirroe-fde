from pydantic import BaseModel
from uuid import UUID
from typing import Tuple

from src.storage.vector import VectorDB
from src.model.runbook import Runbook, UploadRunbookRequest
from src.model.issue import Issue, OpenIssueRequest

from src.core.executor import RunBookExecutor
from src.core.issue_classifier import IssueClassifier


RUNBOOKS = {}  # {rid: runbook}

vector_db = VectorDB()
rb_executor = RunBookExecutor()

issue_classifier = IssueClassifier(vector_db)


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

    Returns some message to send to the user. Might take actions.
    """
    # 1. Find potential runbooks for issue.
    potential_runbooks = issue_classifier.classify(new_issue_request.issue)

    # 2. Call the runbook executor to run the book.
    for rb in potential_runbooks:
        success, response = rb_executor.run_book(
            rb
        )  # This will block at certain points via humanlayer

        if success:
            return response

    # 3. If we're here, we should guardrail this response to send to a human
    return response


def handle_issue_update(issue_update):
    """
    Handle an update to the issue from anyone.

    STRETCH
    """
    pass
