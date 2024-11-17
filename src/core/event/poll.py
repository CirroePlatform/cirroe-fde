"""
    Polls for new issues in a repository. If a new issue is found, or an existing issue is updated,
    it will be handled by the issue handler.
"""

from src.integrations.kbs.github_kb import GithubIntegration
from src.model.issue import Issue, OpenIssueRequest
from include.constants import POLL_INTERVAL
from src.storage.supa import SupaClient
from .handle_issue import debug_issue
from typing import List
import humanlayer
import requests
import asyncio
import time
import os

hl = humanlayer.HumanLayer()

def get_issues_created_or_updated_recently(org_id: str, repo_name: str, github_kb: GithubIntegration) -> List[Issue]:
    """
    Get all issues created in the last POLL_INTERVAL seconds in the provided repo.
    """
    # Get all issues from repo
    issues = github_kb.get_all_issues_json(repo_name, state="open")
    
    # Get current time in seconds
    current_time = time.time()
    
    # Filter to only issues created/updated in last POLL_INTERVAL seconds
    recent_issues = []
    for issue in issues:
        # Convert issue timestamps to seconds since epoch
        created_time = issue["created_at"].timestamp() 
        updated_time = issue["updated_at"].timestamp()
        
        # Check if issue was created or updated within interval
        if (current_time - created_time <= POLL_INTERVAL or 
            current_time - updated_time <= POLL_INTERVAL):
            recent_issues.append(issue)

    # Convert to Issue objects
    recent_issues = [Issue(**issue) for issue in recent_issues]

    return recent_issues


def poll_for_issues(org_id: str, repo_name: str):
    """
    Polls for new issues in a repository. If a new issue is found, or an existing issue is updated,
    it will be handled by the issue handler. Then, we will comment on the issue with the response, guarded 
    by humanlayer.
    """
    github_kb = GithubIntegration(org_id, [repo_name])
    org_name = SupaClient(org_id).get_user_data("org_name")

    while True:
        time.sleep(POLL_INTERVAL)
        print("Polling for issues")

        # 1. Get all issues created or modified in the last POLL_INTERVAL seconds.
        issues = get_issues_created_or_updated_recently(org_id, repo_name, github_kb)

        # 2. call debug_issue for each issue.
        for issue in issues:
            issue_req = OpenIssueRequest(
                issue=issue,
                requestor_id=org_id,
            )
            response = debug_issue(issue_req)
            text_response = response["response"]

            # 3. comment on the issue with the response, guarded by humanlayer. TODO untested, but this shouldn't block the main thread. It should just fire off the coroutine.
            asyncio.run(comment_on_issue(org_id, repo_name, issue, text_response))


@hl.require_approval
async def comment_on_issue(org_name: str, repo: str, issue: Issue, response: str):
    """
    Comments on an issue with the response. Guards with humanlayer.
    """
    url = f"https://api.github.com/repos/{org_name}/{repo}/issues/{issue.ticket_number}/comments"

    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TEST_TOKEN')}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "body": response
    }

    # Post the comment
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()