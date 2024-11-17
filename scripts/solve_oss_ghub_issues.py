"""
A basic script that solves a few subsets of issues from some commercial oss projects.
"""

import random
import logging

from uuid import UUID

from src.integrations.kbs.github_kb import GithubIntegration, Repository
from src.integrations.kbs.issue_kb import IssueKnowledgeBase
from src.integrations.kbs.documentation_kb import DocumentationKnowledgeBase
from src.model.issue import Issue
import tqdm

from include.constants import DEFAULT_TEST_TRAIN_RATIO, CLOSED


# Setup repo, issue, and documentation knowledge bases
async def setup_all_kbs_with_repo(
    org_id: UUID,
    org_name: str,
    repo_name: str,
    docu_url: str,
    index_fraction: float = (1 - DEFAULT_TEST_TRAIN_RATIO),
):
    # 1. Setup all knowledge bases
    github = GithubIntegration(org_id, org_name)
    issue_kb = IssueKnowledgeBase(org_id)
    doc_kb = DocumentationKnowledgeBase(org_id)

    # 2. Index the repository with each knowledge base
    await github.index(Repository(remote="github.com", repository=f"{org_name}/{repo_name}", branch="main"))
    # await doc_kb.index(docu_url)

    # 2.a Index the issues, need to pull all issues from the repo then index only enough to allow for evaluationi
    # logging.info(f"Getting all issues for {org_name}/{repo_name}")
    # issues = github.get_all_issues_json(repo_name, CLOSED)
    # random.shuffle(issues)
    # indexable_issues = issues[: int(len(issues) * index_fraction)]

    # for issue in tqdm.tqdm(
    #     indexable_issues, desc="Indexing issues", total=len(indexable_issues)
    # ):
    #     comments = {}
    #     for comment in issue["comments"]:
    #         comments[comment["user"]["login"]] = comment["body"]

    #     await issue_kb.index(
    #         Issue(
    #             primary_key=str(issue["id"]),
    #             description=f"title: {issue['title']}, description: {issue['body']}",
    #             comments=comments,
    #             org_id=org_id,
    #         )
    #     )


def solve_issue(repo: str, issue_id: int):
    """
    Solves a given issue from a given repository.
    """

    github = GithubIntegration(UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1"), "mem0ai")
    logging.info(github.list_repositories())
