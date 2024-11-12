from include.constants import (
    MEM0AI_ORG_ID,
    MEM0AI_ORG_NAME,
    MEM0AI_REPO_NAME,
)
from test.eval_agent import Orchestrator

orchestrator = Orchestrator(
    MEM0AI_ORG_ID, MEM0AI_ORG_NAME, MEM0AI_REPO_NAME, test_train_ratio=0.2
)
orchestrator.evaluate()
