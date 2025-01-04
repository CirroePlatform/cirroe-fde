"""
A basic script that solves a few subsets of issues from some commercial oss projects.
"""

import random
import logging
from time import sleep

from uuid import UUID

from src.integrations.kbs.documentation_kb import DocumentationKnowledgeBase
from src.integrations.kbs.github_kb import GithubKnowledgeBase, Repository
from src.integrations.kbs.issue_kb import IssueKnowledgeBase
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
    github = GithubKnowledgeBase(org_id, org_name)
    issue_kb = IssueKnowledgeBase(org_id)
    doc_kb = DocumentationKnowledgeBase(org_id)

    # 2. Index the repository with each knowledge base
    # await doc_kb.index(docu_url)
    await github.index(
        Repository(remote="github.com", repository=repo_name, branch="main")
    )

    # 2.a Index the issues, need to pull all issues from the repo then index only enough to allow for evaluationi
    # logging.info(f"Getting all issues for {org_name}/{repo_name}")
    # issues = github.get_all_issues_json(repo_name, CLOSED, include_prs=True)
    # random.shuffle(issues)
    # indexable_issues = issues[: int(len(issues) * index_fraction)]

    # for issue in tqdm.tqdm(
    #     github.json_issues_to_issues(indexable_issues),
    #     desc="Indexing issues",
    #     total=len(indexable_issues),
    # ):
    #     try:
    #         success = await issue_kb.index(issue)
    #         if not success:
    #             logging.error(
    #                 f"Failed to index issue {issue.ticket_number}. Sleeping for 2 seconds..."
    #             )
    #             sleep(2)
    #     except Exception as e:
    #         logging.error(
    #             f"Error indexing issue {issue.ticket_number}: {e}, skipping..."
    #         )
