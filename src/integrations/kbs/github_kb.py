import os
from uuid import UUID
import requests
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from src.model.issue import Issue

from src.integrations.kbs.base_kb import BaseKnowledgeBase, KnowledgeBaseResponse


class Repository(BaseModel):
    remote: str  # e.g. "github.com"
    repository: str  # e.g. "username/repo"
    branch: str = "main"


class LinkGithubRequest(BaseModel):
    org_id: UUID
    org_name: str


class GithubIntegration(BaseKnowledgeBase):
    """
    Integration with Github repositories via Greptile API for code search and analysis.
    """

    def __init__(self, org_id: UUID, org_name: str):
        """
        Initialize Github integration for an organization

        Args:
            org_id: Organization ID to scope the integration
            org_name: Organization name for GitHub API calls
        """
        super().__init__(org_id)
        self.org_name = org_name
        self.api_base = "https://api.greptile.com/v2"

        self.gh_token = os.getenv("GITHUB_TEST_TOKEN")
        if self.gh_token is None:
            self.gh_token = self.get_github_token(org_id)

        self.headers = {
            "Authorization": f"Bearer {os.getenv('GREPTILE_API_KEY')}",
            "X-GitHub-Token": f"{self.gh_token}",
            "Content-Type": "application/json",
        }

    def get_github_token(self, org_id: str) -> str:
        """
        Get the GitHub token for an organization from supabase vault.
        """
        # TODO
        return os.getenv("GITHUB_TEST_TOKEN")

    def get_all_issues_json(
        self, repo_name: str, state: Optional[str] = "closed"
    ) -> Dict[str, Any]:
        """
        Get all issues (excluding pull requests) for some provided repository.
        """
        if "github.com" in repo_name:
            repo_name = "/".join(repo_name.split("/")[-2:])
        else:
            repo_name = repo_name

        # Set up API request
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.getenv('GITHUB_TEST_TOKEN')}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Add parameters to exclude pull requests and filter by state
        params = {"state": state} if state is not None else {}
        # Add filter to exclude pull requests
        url = f"https://api.github.com/repos/{repo_name}/issues"

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        # Filter out pull requests from the response
        issues = [issue for issue in response.json() if "pull_request" not in issue]

        # Fetch comments for each issue
        for issue in issues:
            comments_url = issue["comments_url"]
            comments_response = requests.get(comments_url, headers=headers)
            comments_response.raise_for_status()

            # Add comments to the issue object
            issue["comments"] = comments_response.json()

        return issues

    def index_user(self):
        """
        Index all of the organization's repositories.
        """
        # get users' github token from supabase, set the self.headers['X-GitHub-Token']
        # TODO
        repos = self.list_repositories()
        for repo in repos:
            self.index_repository(repos[repo])

    def list_repositories(self) -> Dict[str, Repository]:
        """
        List all repositories for the organization

        Returns:
            Dict mapping repository names to Repository objects
        """
        url = f"https://api.github.com/orgs/{self.org_name}/repos"
        github_headers = {
            "Authorization": f"Bearer {self.gh_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        page = 1
        repos = []
        while True:
            response = requests.get(
                url, headers=github_headers, params={"per_page": 100, "page": page}
            )
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch repositories: {response.status_code} {response.text}"
                )

            repos.extend(response.json())
            if len(repos) == 0:
                break

            page += 1

        repos_rv = {}
        for github_repo in repos:
            url = f"{self.api_base}/repositories/{github_repo['id']}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                repo_data = response.json()
                name = repo_data["repository"]
                repos_rv[name] = Repository(
                    remote=repo_data["remote"],
                    repository=name,
                    branch=repo_data.get("branch", "main"),
                )

        return repos_rv

    async def index(self, repository: Repository) -> bool:
        """
        Index or reindex a repository for searching

        Args:
            repository: Repository to index

        Returns:
            bool indicating if indexing was successful
        """
        try:
            url = f"{self.api_base}/repositories"

            payload = {
                "remote": repository.remote,
                "repository": repository.repository,
                "branch": repository.branch,
                "reload": False,
                "notify": True,
            }

            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            logging.info(f"Successfully indexed repository: {repository.repository}")
            return True
        except Exception as e:
            logging.error(f"Failed to index repository: {str(e)}")
            return False

    def query(self, query: str, limit: int = 5) -> List[KnowledgeBaseResponse]:
        """
        Search code repositories with natural language queries

        Args:
            query: Natural language query about the codebase
            limit: Maximum number of results to return

        Returns:
            List of KnowledgeBaseResponse objects containing search results
        """
        try:
            repositories = list(self.list_repositories().values())
            url = f"{self.api_base}/query"

            payload = {
                "messages": [{"id": "query", "content": query, "role": "user"}],
                "repositories": [
                    {
                        "remote": repo.remote,
                        "repository": repo.repository,
                        "branch": repo.branch,
                    }
                    for repo in repositories
                ],
                "stream": False,
                "genius": True,
            }

            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            results = response.json()["results"][:limit]
            return [
                KnowledgeBaseResponse(
                    content=result["content"],
                    source=result["file"],
                    score=result.get("score", 0.0),
                )
                for result in results
            ]
        except Exception as e:
            logging.error(f"Failed to query repositories: {str(e)}")
            return []
