from src.integrations.github import GithubIntegration
from src.integrations.issue_kb import IssueKnowledgeBase
from uuid import UUID
from typing import Dict, Any
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

    def __init__(self, requestor_id: UUID, user_git_org_name: str):
        self.requestor_id = requestor_id
        self.github = GithubIntegration(org_id=self.requestor_id, org_name=user_git_org_name)
        self.issue_kb = IssueKnowledgeBase(self.requestor_id)

    def execute_codebase_search(self, problem_description: str, k: int) -> Dict[str, Any]:
        """
            Execute a command over git repos using the Greptile API integration.

        Args:
            problem_description (str): The search query in natural language format.
            k (int): The number of chunks to retrieve from the codebase

        Returns:
            Dict[str, Any]: Results of the search with matches found
        """
        # Execute search via Greptile API
        try:
            response = self.github.search_code(problem_description, [], k=k)
            return response
        except Exception as e:
            return {
                "response": response,
                "error": str(e),
            }

    def execute_issue_search(self, query: str, limit: int) -> Dict[str, Any]:
        """
        Execute a search over the teams historical issues.
        """
        return self.issue_kb.query(query, limit)
