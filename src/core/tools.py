from uuid import UUID
from typing import List, Tuple, Optional
from typeguard import typechecked

from src.integrations.kbs.github_kb import GithubIntegration, Repository
from src.integrations.kbs.issue_kb import IssueKnowledgeBase, KnowledgeBaseResponse
from src.integrations.kbs.documentation_kb import DocumentationKnowledgeBase
from src.integrations.kbs.web_kb import WebKnowledgeBase

from src.storage.supa import SupaClient

from include.constants import ORG_NAME, KnowledgeBaseType


@typechecked
class SearchTools:

    def __init__(self, requestor_id: UUID, github_repos: List[Repository]):
        self.requestor_id = requestor_id
        self.supa = SupaClient(user_id=self.requestor_id)
        self.org_name = self.get_org_name()

        self.github = GithubIntegration(
            org_id=self.requestor_id, org_name=self.org_name, repos=github_repos
        )
        self.issue_kb = IssueKnowledgeBase(self.requestor_id)
        self.documentation_kb = DocumentationKnowledgeBase(self.requestor_id)
        self.web_kb = WebKnowledgeBase(self.requestor_id)

    def get_org_name(self):
        userdata = self.supa.get_user_data(ORG_NAME, debug=True)
        return userdata[ORG_NAME]

    def execute_search(
        self,
        query: str,
        limit: int,
        knowledge_base: str | KnowledgeBaseType,
        traceback: Optional[str] = None,
        user_provided_code: Optional[str] = None,
        user_setup_details: Optional[str] = None,
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
        Execute a search over the codebase, issues, and documentation.

        Args:
            query (str): The search query in natural language format.
            limit (int): The number of results to retrieve
            knowledge_base (KnowledgeBaseType): The knowledge base to use for the search
            traceback (Optional[str]): The traceback to use for cleaning the results
            user_provided_code (Optional[str]): The user provided code to use for cleaning the results
            user_setup_details (Optional[str]): The user setup details to use for cleaning the results
        """
        if isinstance(knowledge_base, str):
            knowledge_base = KnowledgeBaseType(knowledge_base)

        if knowledge_base == KnowledgeBaseType.CODEBASE:
            return self.github.query(
                query, limit, traceback, user_provided_code=user_provided_code, user_setup_details=user_setup_details
            )
        elif knowledge_base == KnowledgeBaseType.ISSUES:
            return self.issue_kb.query(
                query, limit, traceback, user_provided_code=user_provided_code, user_setup_details=user_setup_details
            )
        elif knowledge_base == KnowledgeBaseType.DOCUMENTATION:
            return self.documentation_kb.query(
                query, limit, traceback, user_provided_code=user_provided_code, user_setup_details=user_setup_details
            )
        elif knowledge_base == KnowledgeBaseType.WEB:
            return self.web_kb.query(
                query, limit, traceback, user_provided_code=user_provided_code, user_setup_details=user_setup_details
            )
