from uuid import UUID
from typing import List
from typeguard import typechecked

from src.integrations.kbs.github_kb import GithubIntegration
from src.integrations.kbs.issue_kb import IssueKnowledgeBase, KnowledgeBaseResponse
from src.integrations.kbs.documentation_kb import DocumentationKnowledgeBase

from src.storage.supa import SupaClient

from include.constants import ORG_NAME

DEBUG_ISSUE_TOOLS = [
    {
        "name": "execute_codebase_search",
        "description": "A function to search the teams codebase for relevant code snippets. This will return the top k chunks of code from the teams various codebases relevant to the provided search query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "problem_description": {
                    "type": "string",
                    "description": "A description of an issue from a customer on some ticket",
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of chunks to retrieve from the codebase",
                },
            },
            "required": ["problem_description", "limit"],
        },
    },
    {
        "name": "execute_issue_search",
        "description": "This is a knowledge base of previous issues from users, the response here would contain a list of issues with comments and descriptions from users and engineers, and the whether the issue has been resolved.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A natural language query about previous issues",
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of issues to retrieve",
                },
            },
            "required": ["query", "limit"],
        },
    },
    {
        "name": "execute_documentation_search",
        "description": "A function to search the teams documentation for relevant information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A natural language query about the documentation",
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of documents to retrieve",
                },
            },
            "required": ["query", "limit"],
        },
    },
]

DEBUG_ISSUE_FILE = "include/prompts/debug_issue.txt"


@typechecked
class SearchTools:

    def __init__(self, requestor_id: UUID):
        self.requestor_id = requestor_id
        self.supa = SupaClient(user_id=self.requestor_id)
        self.org_name = self.get_org_name()

        self.github = GithubIntegration(org_id=self.requestor_id, org_name=self.org_name)
        self.issue_kb = IssueKnowledgeBase(self.requestor_id)
        self.documentation_kb = DocumentationKnowledgeBase(self.requestor_id)

    def get_org_name(self):
        userdata = self.supa.get_user_data()
        return userdata[ORG_NAME]

    def execute_codebase_search(
        self, query: str, limit: int
    ) -> List[KnowledgeBaseResponse]:
        """
            Execute a command over git repos using the Greptile API integration.

        Args:
            query (str): The search query in natural language format.
            limit (int): The number of chunks to retrieve from the codebase

        Returns:
            List[KnowledgeBaseResponse]: List of codebase responses that match the search query
        """
        try:
            response = self.github.query(query, limit=limit)
            return response
        except Exception as e:
            return [str(e)]

    def execute_issue_search(
        self, query: str, limit: int
    ) -> List[KnowledgeBaseResponse]:
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
            return [str(e)]

    def execute_documentation_search(
        self, query: str, limit: int
    ) -> List[KnowledgeBaseResponse]:
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
            return [str(e)]
