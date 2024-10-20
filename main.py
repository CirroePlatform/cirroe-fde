from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID

from src.server.handle_actions import handle_new_runbook
from src.integrations.merge import create_link_token, retrieve_account_token

from src.model.runbook import UploadRunbookRequest
from src.model.issue import OpenIssueRequest, WebhookPayload, Issue
from src.model.auth import GetLinkTokenRequest, GetAccountTokenRequest

from src.core.handle_issue import debug_issue

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mapping of issue ids to handler objects
ISSUE_HANDLERS = {}

@app.post("/runbook")
def upload_runbook(
    runbook_req: UploadRunbookRequest, background_tasks: BackgroundTasks
):
    """
    Accepts a new runbook from the frontend, and async adds it to vector db.
    """
    background_tasks.add_task(handle_new_runbook, runbook_req)

@app.post("/issue")
def new_issue(
    payload: WebhookPayload, background_tasks: BackgroundTasks
):
    """
    Handles the case of a new issue being created.

    Triggered from a webhook, so TODO need to send message to user via 
    slack or something.
    """

    requestor = payload.data.end_user.email_address
    tid = payload.hook.id

    # TODO Need to look into passing more data rather than just this basic stuff here...
    problem_description = payload.data.error_description

    issue = Issue(tid=tid, problem_description=problem_description, comments=[])

    req = OpenIssueRequest(
        requestor=requestor,
        issue=issue
    )
    background_tasks.add_task(debug_issue, req)

@app.get("/link_token/{uid}/{org_name}/{email}")
def get_link_token(uid: UUID, org_name: str, email: str):
    """
    Returns a new link token for a brand new integration.
    """
    request = GetLinkTokenRequest(uid=uid, org_name=org_name, email=email)

    print("Entered link token request")
    return create_link_token(request)

@app.post("/account_token")
def create_account_token(request: GetAccountTokenRequest):
    """
    Swaps out a public token for an account token. Should 
    be stored securely on backend.
    """
    print("Entered retrieve acct token request")
    return retrieve_account_token(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app")
