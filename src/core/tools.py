from src.integrations.github import GithubIntegration
from src.integrations.issue_kb import IssueKnowledgeBase, KnowledgeBaseResponse
from uuid import UUID
from typing import Dict, Any, List
from typeguard import typechecked

# TODO implement the rest of the knowledge bases (cloud, documentation, prev issues)

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
                "k": {
                    "type": "integer",
                    "description": "The number of chunks to retrieve from the codebase",
                },
            },
            "required": ["problem_description", "k"],
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
                }
            },  
            "required": ["query", "limit"],
        },
    }
]

DEBUG_ISSUE_FILE = "include/prompts/debug_issue.txt"

@typechecked
class SearchTools:

    def __init__(self, requestor_id: UUID):
        self.requestor_id = requestor_id
        org_name = "CirroePlatform" # TODO: fetch this from users' supabase table

        self.github = GithubIntegration(org_id=self.requestor_id, org_name=org_name)
        self.issue_kb = IssueKnowledgeBase(self.requestor_id)

    def execute_codebase_search(self, query: str, limit: int) -> List[KnowledgeBaseResponse]:
        """
            Execute a command over git repos using the Greptile API integration.

        Args:
            query (str): The search query in natural language format.
            limit (int): The number of chunks to retrieve from the codebase

        Returns:
            List[KnowledgeBaseResponse]: List of codebase responses that match the search query
        """
        # Execute search via Greptile API
        try:
            response = self.github.query(query, limit=limit)
            return response
        except Exception as e:
            return [str(e)]

    def execute_issue_search(self, query: str, limit: int) -> List[KnowledgeBaseResponse]:
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