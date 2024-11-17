"""
    Polls for new issues in a repository. If a new issue is found, or an existing issue is updated,
    it will be handled by the issue handler.
"""

from include.constants import POLL_INTERVAL
from .handle_issue import debug_issue
from src.model.issue import Issue, OpenIssueRequest
import humanlayer
import time
import asyncio
hl = humanlayer.HumanLayer()

def get_issues_created_or_updated_recently(org_id: str, repo_name: str):
    """
    Get all issues created in the last POLL_INTERVAL seconds.
    """
    pass

def poll_for_issues(org_id: str, repo_name: str):
    """
    Polls for new issues in a repository. If a new issue is found, or an existing issue is updated,
    it will be handled by the issue handler. Then, we will comment on the issue with the response, guarded 
    by humanlayer.
    """

    while True:
        time.sleep(POLL_INTERVAL)
        print("Polling for issues")

        # 1. Get all issues created or modified in the last POLL_INTERVAL seconds.
        issues = get_issues_created_or_updated_recently(org_id, repo_name)

        # 2. call debug_issue for each issue.
        for issue in issues:
            issue_req = OpenIssueRequest(
                issue=issue,
                requestor_id=org_id,
            )
            response = debug_issue(issue_req)
            text_response = response["response"]

            # 3. comment on the issue with the response, guarded by humanlayer. TODO untested, but this shouldn't block the main thread. It should just fire off the coroutine.
            asyncio.run(comment_on_issue(issue, text_response))


@hl.require_approval
async def comment_on_issue(issue: Issue, response: str):
    """
    Comments on an issue with the response. Guards with humanlayer.
    """
    pass