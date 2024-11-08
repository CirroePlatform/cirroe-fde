from scripts.solve_oss_ghub_issues import setup_repos
from uuid import UUID
import asyncio


from test.docu_test import test_index_docu_page

test_index_docu_page()

# asyncio.run(setup_repos(MEM0AI_ORG_ID, MEM0AI_REPO))
