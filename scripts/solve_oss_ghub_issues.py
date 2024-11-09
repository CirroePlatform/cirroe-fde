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

from include.constants import MEM0AI_ORG_ID, MEM0AI_DOCU_URL, DEFAULT_TEST_TRAIN_RATIO


# Setup repo, issue, and documentation knowledge bases
async def setup_repos(org_id: UUID, repo_name: str, index_fraction: float = (1 - DEFAULT_TEST_TRAIN_RATIO)):
    # 1. Setup all knowledge bases
    github = GithubIntegration(org_id, repo_name)
    issue_kb = IssueKnowledgeBase(org_id)
    doc_kb = DocumentationKnowledgeBase(org_id)


    # 2. Index the repository with each knowledge base
    await github.index(Repository(remote="github", repository=repo_name, branch="main"))
    await doc_kb.index(MEM0AI_DOCU_URL)

    # 2.a Index the issues, need to pull all issues from the repo then index only enough to allow for evaluationi
    issues = github.get_all_issues_json(repo_name, state=None)

    random.shuffle(issues)
    indexable_issues = issues[:int(len(issues) * index_fraction)]

    for issue in indexable_issues:
        comments = {}
        for comment in issue["comments"]:
            comments[comment["user"]["login"]] = comment["body"]

        await issue_kb.index(
            Issue(
                primary_key=str(issue["id"]),
                description=f"title: {issue['title']}, description: {issue['body']}",
                comments=comments,
                org_id=MEM0AI_ORG_ID,
            )
        )


def solve_issue(repo: str, issue_id: int):
    """
    Solves a given issue from a given repository.
    """

    github = GithubIntegration(UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1"), "mem0ai")
    logging.info(github.list_repositories())
