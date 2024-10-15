from pydantic import BaseModel
from uuid import UUID
from typing import Tuple, List
import openai 

from src.storage.vector import VectorDB
from src.model.runbook import Runbook, UploadRunbookRequest
from src.model.issue import Issue, OpenIssueRequest

from src.core.executor import RunBookExecutor
from src.core.issue_classifier import IssueClassifier


RUNBOOKS = {}  # {rid: runbook}

COALESCE_RESPONSE_FILE = "include/prompts/coalesce_response.txt"

vector_db = VectorDB()
rb_executor = RunBookExecutor()

issue_classifier = IssueClassifier(vector_db)

client = openai.OpenAI()

class IssueUpdateRequest(BaseModel):
    issue: Issue
    new_comment: Tuple[UUID, str]

# humanlayer this with an option for the slack mf to change up the data sent back to the user.
def coalesce_stepwide_responses(responses: List[str], rb: Runbook, issue_req: OpenIssueRequest) -> str:
    """
    Given a set of responses from executing some runbook, the issue from the user,
    and the runbook used, coalesce one final response to the user.
    """
    with open(COALESCE_RESPONSE_FILE, "r", encoding="utf8") as fp:
        sysprompt = fp.read()

        prompt = ""
        for i, step in enumerate(rb.steps):
            prompt += f"step {i} was {step.description}, output was {responses[i]}"

        final_prompt = f"""
        {sysprompt}
        
        issue requestor: {issue_req.requestor}
        issue description: {issue_req.issue.problem_description}

        runbook steps and outputs:
        {prompt}
        """

        messages = [{"role": "user", "content": final_prompt}]

        response = client.chat.completions.create(
            model="o1-preview",
            messages=messages,
        )

        return response.choices[0].message.content


def handle_new_runbook(runbook_req: UploadRunbookRequest):
    """
    Called from the server endpoint, handles a new runbook request
    """
    if runbook_req.runbook.rid not in RUNBOOKS:
        vector_db.add_runbook(runbook_req.runbook)


def handle_new_issue(new_issue_request: OpenIssueRequest) -> str:
    """
    Handle a new inbound issue filed.

    Returns some message to send to the user. Might take actions.
    """
    # 1. Find potential runbooks for issue.
    potential_runbooks = issue_classifier.classify(new_issue_request.issue)

    # 2. Call the runbook executor to run the book.
    for rb in potential_runbooks:
        success, responses = rb_executor.run_book(
            rb
        )  # This will block at certain points via humanlayer

        if success:
            return coalesce_stepwide_responses(responses, rb, new_issue_request)

    # 3. If we're here, we failed to execute. tuff.
    raise ValueError("Couldn't figure out user issue")


def handle_issue_update(issue_update):
    """
    Handle an update to the issue from anyone.

    STRETCH
    """
    pass
