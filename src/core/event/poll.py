"""
    Polls for new issues in a repository. If a new issue is found, or an existing issue is updated,
    it will be handled by the issue handler.
"""

from src.integrations.kbs.github_kb import GithubIntegration, Repository
from src.model.issue import Issue, OpenIssueRequest
from include.constants import POLL_INTERVAL
from datetime import datetime, timedelta
from src.storage.supa import SupaClient
from .handle_issue import debug_issue
from typing import List
import requests
import logging
import asyncio
import time
import os

def get_issues_created_or_updated_recently(org_id: str, repo_name: str, github_kb: GithubIntegration) -> List[Issue]:
    """
    Get all issues created in the last POLL_INTERVAL seconds in the provided repo.
    """
    # Get all issues from repo
    issues = github_kb.get_all_issues_json(repo_name, state="open")
    
    # Get current time in seconds
    current_time = datetime.now()
    
    # Convert POLL_INTERVAL to a timedelta
    poll_interval_timedelta = timedelta(seconds=POLL_INTERVAL)

    # Filter to only issues created/updated in last POLL_INTERVAL seconds
    recent_issues = []
    for issue in issues:
        # Convert issue timestamps to seconds since epoch
        created_time = issue["created_at"] 
        updated_time = issue["updated_at"]

        created_time = datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%SZ")
        updated_time = datetime.strptime(updated_time, "%Y-%m-%dT%H:%M:%SZ")

        # Check if issue was created or updated within interval
        if (current_time - created_time <= poll_interval_timedelta or 
            current_time - updated_time <= poll_interval_timedelta):
            recent_issues.append(issue)

    # Convert to Issue objects
    recent_issues = [Issue(**issue) for issue in recent_issues]

    return recent_issues


def poll_for_issues(org_id: str, repo_name: str, debug: bool = False):
    """
    Polls for new issues in a repository. If a new issue is found, or an existing issue is updated,
    it will be handled by the issue handler. Then, we will comment on the issue with the response, guarded 
    by humanlayer.

    TODO issue fetches are slowing this function down, we should most likely try to cache existing issues or only query by time period per poll.
    """

    org_name = SupaClient(org_id).get_user_data("org_name")["org_name"]
    github_kb = GithubIntegration(org_id, org_name, repo_names=[repo_name])
    on_init = True
    repo_obj = Repository(remote="github.com", repository=repo_name, branch="main")

    while True:
        processing_start_time = time.time()
        logging.info("Polling for issues")

        # 1. Get all issues created or modified in the last POLL_INTERVAL seconds. If this is the first time we're polling, we want to get all unsolved issues, regardless of time.
        if not on_init:
            issues = get_issues_created_or_updated_recently(org_id, repo_name, github_kb)
        else:
            issues = github_kb.get_all_issues_json(repo_name, state="open") # TODO add a logging msg here.
            on_init = False

        # 2. call debug_issue for each issue.
        issue_objs = github_kb.json_issues_to_issues(issues)
        for issue in issue_objs:
            issue_req = OpenIssueRequest(
                issue=issue,
                requestor_id=org_id,
            )
            
            response = debug_issue(issue_req, [repo_obj])
            text_response = response["response"]

            # 3. comment on the issue with the response, guarded by humanlayer. TODO untested, but this shouldn't block the main thread. It should just fire off the coroutine.
            asyncio.run(comment_on_issue(org_name, repo_name, issue, text_response))
        
        if debug:
            break

        # 4. Sleep for POLL_INTERVAL seconds. If our poll interval is longer than the processing time, don't sleep at all.
        processing_time = time.time() - processing_start_time
        if processing_time > POLL_INTERVAL:
            logging.warning(f"Poll interval of {POLL_INTERVAL} seconds exceeded by {processing_time} seconds. Skipping sleep.")
        
        time.sleep(max(0, POLL_INTERVAL - processing_time))

async def comment_on_issue(org_name: str, repo: str, issue: Issue, response: str):
    """
    Comments on an issue with the response.
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