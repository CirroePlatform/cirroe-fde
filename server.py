from fastapi import FastAPI, BackgroundTasks
import uvicorn

from src.server.handle_actions import handle_new_runbook

from src.model.runbook import UploadRunbookRequest
from src.model.issue import IssueReq

app = FastAPI()

# Mapping of issue ids to handler objects
ISSUE_HANDLERS = {}

@app.post("/runbook")
def upload_runbook(runbook_req: UploadRunbookRequest, background_tasks: BackgroundTasks):
    """
    Accepts a new runbook from the frontend, and async adds it to vector db.
    """
    background_tasks.add_task(handle_new_runbook, runbook_req)

def handle_new_issue(issue_req: )

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
