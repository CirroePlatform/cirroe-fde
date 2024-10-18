from fastapi import FastAPI, BackgroundTasks
import uvicorn

from src.server.handle_actions import handle_new_runbook, handle_new_issue
from src.integrations.merge import create_link_token

from src.model.runbook import UploadRunbookRequest
from src.model.issue import OpenIssueRequest
from src.model.auth import GetLinkTokenRequest

app = FastAPI()

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
    issue_open: OpenIssueRequest
):
    """
    Handles the case of a new issue being created.
    
    Returns a response to send to the user.
    """
    return handle_new_issue(issue_open)

@app.get("/link_token")
def get_link_token(request: GetLinkTokenRequest):
    """
    Returns a new link token for a brand new integration.
    """
    return create_link_token(request)


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
