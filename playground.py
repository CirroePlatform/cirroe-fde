from include.constants import MEM0AI_ORG_ID, MEM0AI_REPO_NAME, MEM0AI_ORG_NAME, MEM0AI_DOCU_URL
from scripts.solve_oss_ghub_issues import setup_all_kbs_with_repo
import asyncio

# org_id: UUID, org_name: str, repo_name: str, docu_url: str
asyncio.run(setup_all_kbs_with_repo(MEM0AI_ORG_ID, MEM0AI_ORG_NAME, MEM0AI_REPO_NAME, MEM0AI_DOCU_URL))