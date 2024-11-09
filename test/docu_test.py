from src.integrations.kbs.documentation_kb import DocumentationKnowledgeBase
from src.storage.vector import VectorDB
import asyncio
from src.model.documentation import DocumentationPage
from uuid import UUID

from include.constants import MEM0AI_ORG_ID, MEM0AI_DOCU_URL

docu_pkey = UUID("1f763b2f-256d-41f8-a473-444c55a4ced7")
docu_kb = DocumentationKnowledgeBase(MEM0AI_ORG_ID)
vector_db = docu_kb.vector_db
vector_db.is_debug_mode = True

def test_index_docu_page():
    page = DocumentationPage(primary_key=docu_pkey, url=MEM0AI_DOCU_URL, content="Test content")
    
    vector_db.add_documentation_page(page)

    all_docs = vector_db.get_all_documentation([docu_pkey])
    assert any(doc.primary_key == docu_pkey for doc in all_docs)
    
async def test_index_docu_via_kb():
    success = await docu_kb.index(MEM0AI_DOCU_URL)

    assert success