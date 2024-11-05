from src.integrations.documentation_kb import DocumentationKnowledgeBase
from uuid import UUID

async def test_idx():
    org_id = UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1")
    kb = DocumentationKnowledgeBase(org_id)

    oss_repos_docs = [
        "https://docs.letta.com/",
        "https://trypear.ai/docs",
        "https://docs.mem0.ai/",
    ]

    for repo in oss_repos_docs:
        await kb.index(repo)