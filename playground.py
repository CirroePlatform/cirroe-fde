from scripts.solve_oss_ghub_issues import setup_all_kbs_with_repo
from src.storage.supa import SupaClient
from test.eval_agent import Orchestrator
from src.integrations.kbs.github_kb import GithubIntegration
from uuid import UUID
import asyncio

from include.constants import TRIGGER_ORG_ID, REPO_NAME


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
        TRIGGER_ORG_ID
    ]
    for org in orgs:
        # 1. get repo info
        supa = SupaClient(org)
        repo_info = supa.get_user_data(
            "org_name", REPO_NAME, "repo_url", "docu_url", debug=True
        )

        # 2. evaluate and save results
        evaluate(org, repo_info["org_name"], repo_info[REPO_NAME], test_train_ratio=0.2, enable_labels=True)