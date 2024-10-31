import os
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class Repository:
    remote: str  # e.g. "github.com"
    repository: str  # e.g. "username/repo"
    branch: str = "main"

class LinkGithubRequest(BaseModel):
    token: str

class GithubIntegration:
    """
    Integration with Github repositories via Greptile API for code search and analysis.
    """
    
    def __init__(self, org_id: str):
        """
        Initialize Github integration for an organization
        
        Args:
            org_id: Organization ID to scope the integration
        """
        self.org_id = org_id
        self.api_base = "https://api.greptile.com/v2"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('GREPTILE_API_KEY')}",
            "X-GitHub-Token": f"{os.getenv('GITHUB_TOKEN')}", # TODO retrieve from user. Supabase table should have github token.
            "Content-Type": "application/json"
        }

    def list_repositories(self) -> Dict[str, Repository]:
        """
        List all repositories for the organization
        
        Returns:
            Dict mapping repository names to Repository objects
        """
        # First get repo list from GitHub API
        github_api = "https://api.github.com"
        github_headers = {
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get org repos from GitHub
        github_response = requests.get(
            f"{github_api}/user/repos",
            headers=github_headers
        )
        github_response.raise_for_status()
        
        repos = {}
        for github_repo in github_response.json():
            # Get detailed repo info from Greptile
            url = f"{self.api_base}/repositories/{github_repo['id']}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                repo_data = response.json()
                name = repo_data["repository"]
                repos[name] = Repository(
                    remote=repo_data["remote"],
                    repository=name,
                    branch=repo_data.get("branch", "main")
                )
            
        return repos

    def index_repository(self, repository: Repository, reload: bool = False) -> Dict[str, Any]:
        """
        Index or reindex a repository for searching
        
        Args:
            repository: Repository to index
            reload: Whether to force reindex if already indexed
            
        Returns:
            Dict with indexing status and details
        """
        url = f"{self.api_base}/repositories"
        
        payload = {
            "remote": repository.remote,
            "repository": repository.repository, 
            "branch": repository.branch,
            "reload": reload,
            "notify": True
        }

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def search_code(self, 
                   query: str,
                   repositories: List[Repository],
                   session_id: Optional[str] = None,
                   stream: bool = False,
                   genius: bool = False) -> Dict[str, Any]:
        """
        Search code repositories with natural language queries
        
        Args:
            query: Natural language query about the codebase
            repositories: List of repositories to search
            session_id: Optional session ID for continuity
            stream: Whether to stream results
            genius: Whether to use enhanced search
            
        Returns:
            Dict containing search results with code references
        """
        url = f"{self.api_base}/query"
        
        payload = {
            "messages": [
                {
                    "id": "query",
                    "content": query,
                    "role": "user"
                }
            ],
            "repositories": [
                {
                    "remote": repo.remote,
                    "repository": repo.repository,
                    "branch": repo.branch
                } for repo in repositories
            ],
            "sessionId": session_id,
            "stream": stream,
            "genius": genius
        }

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()