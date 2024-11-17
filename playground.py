from scripts.solve_oss_ghub_issues import setup_all_kbs_with_repo
import asyncio
from include.constants import (
    MEM0AI_ORG_ID,
    MEM0AI_ORG_NAME,
    MEM0AI_REPO_NAME,
    MEM0AI_DOCU_URL,
    BASETEN_ORG_ID,
    BASETEN_ORG_NAME,
    BASETEN_REPO_NAME,
    BASETEN_DOCU_URL,
    QDRANT_ORG_ID,
    QDRANT_ORG_NAME,
    QDRANT_REPO_NAME,
    QDRANT_DOCU_URL,
)
from uuid import UUID
from test.eval_agent import Orchestrator


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
    # random sampling of 10% enabled at the moment.
    evaluate(MEM0AI_ORG_ID, MEM0AI_ORG_NAME, MEM0AI_REPO_NAME, enable_labels=True)
    evaluate(
        BASETEN_ORG_ID,
        BASETEN_ORG_NAME,
        BASETEN_REPO_NAME,
        enable_labels=False,
        test_train_ratio=0.99,
    )
    evaluate(QDRANT_ORG_ID, QDRANT_ORG_NAME, QDRANT_REPO_NAME, test_train_ratio=0.01)
