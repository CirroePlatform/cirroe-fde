from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID

from src.model.issue import (
    OpenIssueRequest,
    WebhookPayload,
    Issue,
    IndexAllIssuesRequest,
)
from src.integrations.kbs.github_kb import LinkGithubRequest, GithubIntegration
from src.core.event.handle_issue import debug_issue, index_all_issues_async

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/link_github")
def link_github(payload: LinkGithubRequest, background_tasks: BackgroundTasks):
    """
    Accepts a new GitHub user id from the frontend, signifying that a user
    has linked their GitHub account and it's ready to be indexed.
    """
    github = GithubIntegration(payload.org_id, payload.org_name)
    background_tasks.add_task(github.index_user)


@app.post("/issue")
def new_issue(payload: WebhookPayload, background_tasks: BackgroundTasks):
    """
    Handles the case of a new issue being created. Triggered from a merge api webhook
    """

    requestor = payload.data.end_user.email_address
    tid = payload.hook.id
    problem_description = payload.data.error_description
    org_id = (
        payload.data.end_user.organization_name
    )  # TODO we need to verify this id is the same loaded into the vector DB.

    issue = Issue(
        primary_key=str(tid),
        description=problem_description,
        comments={},
        org_id=org_id,
    )

    req = OpenIssueRequest(requestor_id=requestor, issue=issue)
    background_tasks.add_task(debug_issue, req)


@app.post("/idx_all_issues")
def index_all_issues(request: IndexAllIssuesRequest, background_tasks: BackgroundTasks):
    """
    Indexes all issues in the database.

    Asynchronusly does this on repeat.
    """
    background_tasks.add_task(index_all_issues_async, request.org_id)
