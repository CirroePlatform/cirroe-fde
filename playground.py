from scripts.solve_oss_ghub_issues import setup_repos
from uuid import UUID
import asyncio

MEM0AI_ORG_ID = UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1")
MEM0AI_REPO = "https://github.com/mem0ai/mem0"

asyncio.run(setup_repos(MEM0AI_ORG_ID, MEM0AI_REPO))
