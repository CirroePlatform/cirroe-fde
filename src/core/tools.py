from uuid import UUID
from typing import List, Tuple, Optional
from typeguard import typechecked

from src.integrations.kbs.github_kb import GithubIntegration, Repository
from src.integrations.kbs.issue_kb import IssueKnowledgeBase, KnowledgeBaseResponse
from src.integrations.kbs.documentation_kb import DocumentationKnowledgeBase

from src.storage.supa import SupaClient

from include.constants import ORG_NAME


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

    def get_org_name(self):
        userdata = self.supa.get_user_data()
        return userdata[ORG_NAME]

    def execute_codebase_search(
        self, query: str, limit: int, traceback: Optional[str] = None
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
            Execute a command over git repos using the Greptile API integration.

        Args:
            query (str): The search query in natural language format.
            limit (int): The number of chunks to retrieve from the codebase
            traceback (Optional[str]): The traceback to use for cleaning the results

        Returns:
            List[KnowledgeBaseResponse]: List of codebase responses that match the search query
        """
        try:
            response = self.github.query(query, limit=limit, tb=traceback)
            return response
        except Exception as e:
            return [], str(e)

    def execute_issue_search(
        self, query: str, limit: int
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
        Execute a search over the teams historical issues.

        Args:
            query (str): The search query in natural language format.
            limit (int): The number of issues to retrieve

        Returns:
            List[KnowledgeBaseResponse]: List of issues that match the search query
        """
        try:
            return self.issue_kb.query(query, limit)
        except Exception as e:
            return [], str(e)

    def execute_documentation_search(
        self, query: str, limit: int
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
        Execute a search over the teams documentation.

        Args:
            query (str): The search query in natural language format.
            limit (int): The number of documents to retrieve

        Returns:
            List[KnowledgeBaseResponse]: List of documentation responses that match the search query
        """
        try:
            return self.documentation_kb.query(query, limit)
        except Exception as e:
            return [], str(e)
