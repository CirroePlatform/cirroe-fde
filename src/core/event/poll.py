"""
    Polls for new issues in a repository. If a new issue is found, or an existing issue is updated,
    it will be handled by the issue handler.
"""

from include.constants import (
    POLL_INTERVAL,
    BUG_LABELS,
    REQUIRES_DEV_TEAM_PROMPT,
    GITHUB_API_BASE,
    CIRROE_USERNAME,
    ABHIGYA_USERNAME,
)
from src.integrations.kbs.github_kb import GithubIntegration, Repository
from src.core.event.user_actions.handle_issue import HandleIssue
from src.model.issue import Issue, OpenIssueRequest
from include.finetune import DatasetCollector
from datetime import datetime, timedelta
from src.storage.supa import SupaClient
from cerebras.cloud.sdk import Cerebras
from typing import List, Optional
from discord.ext import commands
from uuid import UUID
import humanlayer
import requests
import logging
import discord
import asyncio
import json
import time
import os

from include.constants import CHANNEL

hl = humanlayer.HumanLayer()

cerebras_client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))
disc_token = os.getenv("DISCORD_TOKEN")
dataset_collector = DatasetCollector()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Bot is ready to answer questions!")


@bot.event
async def on_message(message):
    # Ignore messages from the bot itself.
    if message.author == bot.user:
        return

    # Check if the message is from the desired channel.
    if message.channel.name == CHANNEL:
        user_question = message.content

        # Example response logic
        if "hello" in user_question.lower():
            await message.channel.send(f"Hello, {message.author.mention}!")
        else:
            await message.channel.send(
                f"I'm not sure how to respond to that yet, {message.author.mention}."
            )


def get_issues_created_or_updated_recently(
    repo_name: str, github_kb: GithubIntegration
) -> List[Issue]:
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
        if (
            current_time - created_time <= poll_interval_timedelta
            or current_time - updated_time <= poll_interval_timedelta
        ):
            recent_issues.append(issue)

    # Convert to Issue objects
    recent_issues = [Issue(**issue) for issue in recent_issues]

    return recent_issues


def issue_needs_dev_team(
    issue: Issue, labels: List[str], consider_labels: bool = True
) -> bool:
    """
    Determine if an issue needs the dev team based on its labels. If there are no labels, then we consider the description.

    Returns True if the issue needs the dev team, False otherwise.
    """
    if (
        consider_labels
        and len(labels) > 0
        and not (any(label in labels for label in BUG_LABELS))
    ):
        return False

    # If there are no labels, we need to determine if the issue is a bug based on the description.
    with open(REQUIRES_DEV_TEAM_PROMPT, "r") as f:
        prompt = f.read()

    chat_completion = cerebras_client.chat.completions.create(
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"<issue_description>{issue.description}</issue_description>",
            },
            *[
                {
                    "role": "user",
                    "content": f"<comment>{json.dumps(comment.model_dump_json())}</comment>",
                }
                for comment in issue.comments
            ],
        ],
        model="llama3.1-8b",
        max_tokens=256,
    )

    # Guard with humanlayer
    # approval = hl.fetch_approval(
    #     humanlayer.FunctionCallSpec(
    #         fn="issue needs a dev team's response",
    #         kwargs={
    #             "issue description": issue.description,
    #             "issue labels": labels,
    #             "any possible comments": issue.comments,
    #             "decision": chat_completion.choices[0].message.content,
    #         },
    #     ),
    # )

    decision = chat_completion.choices[0].message.content.lower() == "yes"
    # completed = approval.as_completed()
    # if (
    #     not completed.approved
    # ):  # if the action is not approved, we want to do the opposite of the model's decision.
    #     decision = not decision

    # For later model training
    # completion_comment = completed.comment
    # dataset_collector.collect_needs_dev_team_output(
    #     issue, actual_decision=decision, additional_info=completion_comment
    # )

    return decision


def poll_for_issues(
    org_id: UUID,
    repo_name: str,
    debug: bool = False,
    ticket_numbers: Optional[set[str]] = None,
):
    """
    Polls for new issues in a repository. If a new issue is found, or an existing issue is updated,
    it will be handled by the issue handler. Then, we will comment on the issue with the response, guarded
    by humanlayer.

    TODO issue fetches are slowing this function down, we should most likely try to cache existing issues or only query by time period per poll.
    """

    org_name = SupaClient(org_id).get_user_data("org_name", debug=debug)["org_name"]
    github_kb = GithubIntegration(
        org_id,
        org_name,
        repos=[Repository(remote="github.com", repository=repo_name, branch="main")],
    )
    on_init = True
    handle_issue = HandleIssue(org_id)

    while True:
        processing_start_time = time.time()
        logging.info("Polling for issues")

        # 1. Get all issues created or modified in the last POLL_INTERVAL seconds. If this is the first time we're polling, we want to get all unsolved issues, regardless of time.
        if not on_init:
            issues = get_issues_created_or_updated_recently(repo_name, github_kb)
        else:
            issues = github_kb.get_all_issues_json(repo_name, state="open")
            logging.info(
                f"Polling for EVERY issue in {repo_name}. Found {len(issues)} issues."
            )
            on_init = False

        # 2. call debug_issue for each issue.
        issue_objs = github_kb.json_issues_to_issues(issues)
        for issue in issue_objs:
            if ticket_numbers and str(issue.ticket_number) not in ticket_numbers:
                continue

            # Get the labels for the issue to help classify whether we should handle it or not.
            # issue_labels = github_kb.get_labels(
            #     issue.ticket_number,
            #     f"{GITHUB_API_BASE}/repos/{org_name}/{repo_name}/issues",
            # )

            last_commenter = (
                issue.comments[-1].requestor_name if issue.comments else None
            )
            last_issue_was_from_cirr0e = (
                last_commenter == CIRROE_USERNAME or last_commenter == ABHIGYA_USERNAME
            )
            if last_issue_was_from_cirr0e:
                # last_issue_was_from_cirr0e or issue_needs_dev_team(
                #     issue, issue_labels, False
                # ):
                logging.info(
                    f"Issue {issue.ticket_number} needs the dev team, not something we should handle. Skipping..."
                )
                continue

            issue_req = OpenIssueRequest(
                issue=issue,
                requestor_id=org_id,
            )

            response = handle_issue.debug_issue(issue_req)
            text_response = response["response"]

            # 3. comment on the issue with the response, guarded by humanlayer. TODO untested, but this shouldn't block the main thread. It should just fire off the coroutine.
            asyncio.run(comment_on_issue(org_name, repo_name, issue, text_response))

        if debug:
            break

        # 4. Sleep for POLL_INTERVAL seconds. If our poll interval is longer than the processing time, don't sleep at all.
        processing_time = time.time() - processing_start_time
        if processing_time > POLL_INTERVAL:
            logging.warning(
                f"Poll interval of {POLL_INTERVAL} seconds exceeded by {processing_time} seconds. Skipping sleep."
            )

        time.sleep(max(0, POLL_INTERVAL - processing_time))


async def comment_on_issue(org_name: str, repo: str, issue: Issue, response: str):
    """
    Comments on an issue with the response.
    """
    url = f"https://api.github.com/repos/{org_name}/{repo}/issues/{issue.ticket_number}/comments"

    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TEST_TOKEN')}",
        "Accept": "application/vnd.github+json",
    }

    data = {"body": response}

    # Post the comment
    # response = requests.post(url, json=data, headers=headers)
    # response.raise_for_status()
    print(data)    
