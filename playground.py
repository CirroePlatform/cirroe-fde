from scripts.solve_oss_ghub_issues import setup_all_kbs_with_repo
from src.core.event.poll import poll_for_issues
from src.storage.supa import SupaClient
from test.eval_agent import Orchestrator
from src.integrations.kbs.github_kb import GithubIntegration
from uuid import UUID
import asyncio
from test.traceback_test import test_clean_traceback

from include.constants import (
    UNSLOTH_ORG_ID,
    MEM0AI_ORG_ID,
    TRIGGER_ORG_ID,
    MILVUS_ORG_ID,
    UEBERDOSIS_ORG_ID,
)


def evaluate(
    org_id: UUID,
    org_name: str,
    repo_name: str,
    test_train_ratio: float = 0.2,
    enable_labels: bool = True,
):
    orchestrator = Orchestrator(
        org_id,
        org_name,
        repo_name,
        test_train_ratio=test_train_ratio,
        enable_labels=enable_labels,
    )
    orchestrator.evaluate()


def index(org_id: UUID, org_name: str, repo_name: str, docu_url: str):
    asyncio.run(setup_all_kbs_with_repo(org_id, org_name, repo_name, docu_url))


if __name__ == "__main__":
    orgs = [
        UNSLOTH_ORG_ID,
        MEM0AI_ORG_ID,
        TRIGGER_ORG_ID,
        MILVUS_ORG_ID,
        UEBERDOSIS_ORG_ID,
    ]

    for org in orgs:
        # 1. get repo info
        supa = SupaClient(org)
        repo_info = supa.get_user_data("repo_name", "repo_url", "docu_url")

        # 2. index repo
        index(org, repo_info["org_name"], repo_info["repo_name"], repo_info["docu_url"])

        # 3. poll for issues
        poll_for_issues(org, repo_info["repo_name"], debug=True)
