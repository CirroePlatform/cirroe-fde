import os
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class Repository:
    remote: str  # e.g. "github.com"
    repository: str  # e.g. "username/repo"
    branch: str = "main"

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
            "X-GitHub-Token": f"{os.getenv('GITHUB_TOKEN')}", # TODO retrieve from user
            "Content-Type": "application/json"
        }

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
                   stream: bool = True,
                   genius: bool = True) -> Dict[str, Any]:
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

    def execute_command(self, command_type: str, query: str) -> Dict[str, Any]:
        """
        Execute a code search command
        
        Args:
            command_type: Type of search (e.g. "code", "description")
            query: Search query
            
        Returns:
            Dict with search results
        """
        # Default repository for the org
        default_repo = Repository(
            remote="github.com",
            repository=f"{self.org_id}/main-repo"  # Adjust based on org structure
        )
        
        return self.search_code(
            query=f"{command_type}: {query}",
            repositories=[default_repo]
        )
