from src.integrations.kbs.documentation_kb import DocumentationKnowledgeBase
from src.storage.vector import VectorDB
from src.model.documentation import DocumentationPage
import uuid

from include.constants import MEM0AI_ORG_ID, MEM0AI_DOCU_URL

# TODO use this space to test out the documentation and vector functions for documentation you just created.

def test_index_docu_page():
    docu_kb = DocumentationKnowledgeBase(MEM0AI_ORG_ID)
    vector_db = docu_kb.vector_db
    page = DocumentationPage(primary_key=uuid.uuid4(), url=MEM0AI_DOCU_URL, content="Test content")

    vector_db.is_debug_mode = True
    vector_db.add_documentation_page(page)
    
    all_docs = set(vector_db.get_all_documentation())
    assert page in all_docs