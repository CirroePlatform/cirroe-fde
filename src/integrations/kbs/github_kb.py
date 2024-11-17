import os
import traceback
import time
from uuid import UUID
import requests
from typeguard import typechecked
import logging
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel

from src.storage.supa import SupaClient
from src.storage.vector import VectorDB
from src.integrations.kbs.base_kb import BaseKnowledgeBase, KnowledgeBaseResponse
from include.constants import INDEX_WITH_GREPTILE, GITHUB_API_BASE
from src.model.code import CodePage, CodePageType


class Repository(BaseModel):
    remote: str  # e.g. "github.com"
    repository: str  # e.g. "username/repo"
    branch: str = "main"


class LinkGithubRequest(BaseModel):
    org_id: UUID
    org_name: str


# This is basically a wrapper around a code page type that allows us to perform tree operations.
class Node:
    def __init__(
        self,
        primary_key: str,
        org_id: str,
        name: str,
        page_type: CodePageType,
        children_ids: List[str],
        summary: Optional[str] = None,
        code_content: Optional[str] = None,
    ) -> None:
        self.data = CodePage(
            primary_key=primary_key,
            org_id=org_id,
            page_type=page_type,
            name=name,
            vector=[],
            summary=summary,
            code_content=code_content,
        )
        self.children_ids = children_ids


class GithubIntegration(BaseKnowledgeBase):
    """
    Integration with Github repositories via Greptile API for code search and analysis.
    """

    def __init__(
        self,
        org_id: UUID,
        org_name: str,
        repos: Optional[List[Repository]] = None,
        repo_names: Optional[List[str]] = None,
    ):
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
        self.repos = repos
        self.treenode_cache: Dict[str, Node] = {}
        
        self.supa_client = SupaClient(self.org_id)
        self.vector_db = VectorDB(self.org_id)

    def get_github_token(self, org_id: str) -> str:
        """
        Get the GitHub token for an organization from supabase vault.
        """
        # TODO
        return os.getenv("GITHUB_TEST_TOKEN")

    def get_all_issues_json(
        self,
        repo_name: str,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get all issues (excluding pull requests) for some provided repository.

        Args:
            repo_name: Name of repository to fetch issues from
            state: Optional filter for issue state (open, closed)
            labels: Optional list of label names to filter issues by
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

        # Add parameters to exclude pull requests and filter by state and labels
        params = {"per_page": 100, "page": 1}
        if state is not None:
            params["state"] = state

        url = f"https://api.github.com/repos/{self.org_name}/{repo_name}/issues"

        all_issues = []
        while True:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            content = response.json()

            # Filter out pull requests from the response
            issues = [issue for issue in content if "pull_request" not in issue]
            final_issues = []

            # Fetch comments for each issue
            for i in range(len(issues)):

                # Get labels if they exist, and remove this from the set if it doesn't satisfy label constraints
                issue_number = issues[i]["number"]

                comments_url = issues[i]["comments_url"]
                try:
                    comments_response = requests.get(comments_url, headers=headers)
                    comments_response.raise_for_status()

                    # Add comments to the issue object
                    issues[i]["comments"] = comments_response.json()
                except (
                    requests.exceptions.Timeout or requests.exceptions.RateLimitError
                ) as e:  # TODO this handler and catch is untested.
                    logging.error(
                        f"request timed out or was rate limited. Sleeping for a few secs then retrying. {e}"
                    )
                    logging.error(traceback.format_exc())
                    time.sleep(10)
                    i -= 1

                should_add = True
                if labels is not None:
                    should_add = False
                    label_url = f"{url}/{issue_number}/labels"
                    label_response = requests.get(label_url, headers=headers)
                    label_response.raise_for_status()

                    issue_labels = set(
                        [label["name"] for label in label_response.json()]
                    )

                    if set(labels).intersection(issue_labels):
                        should_add = True

                if should_add:
                    final_issues.append(issues[i])

            all_issues.extend(final_issues)

            # Check if we've received all issues
            if len(content) < params["per_page"]:
                break

            params["page"] += 1

        return all_issues

    def index_user(self):
        """
        Index all of the organization's repositories.
        """
        # get users' github token from supabase, set the self.headers['X-GitHub-Token']
        # TODO
        repos = self.repos
        for repo in repos:
            self.index(repo)

    def list_repositories(
        self, repo_names: Optional[List[str]] = None, max_repos: int = 30
    ) -> Dict[str, Repository]:
        """
        List repositories for the organization

        Args:
            repo_names: Optional list of repository names to filter by. If None, lists all repositories.
            max_repos: Maximum number of repositories to request. Defaults to 300.

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
            if len(repos) == 0 or len(repos) >= max_repos:
                break

            page += 1

        # Trim to max_repos if we exceeded it
        repos = repos[:max_repos]

        repos_rv = {}
        for github_repo in repos:
            # Skip if repo_names is specified and this repo is not in the list
            if repo_names and github_repo["name"] not in repo_names:
                continue

            url = f"{self.api_base}/repositories/{github_repo['id']}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                repo_data = response.json()
                name = repo_data["repository"]

                repos_rv[name] = Repository(
                    remote="github.com",
                    repository=name,
                    branch=repo_data.get("branch", "main"),
                )

        return repos_rv

    def index_greptile(self, repository: Repository) -> bool:
        """
        Index a repository with Greptile
        """
        try:
            url = f"{self.api_base}/repositories"

            payload = {
                "remote": repository.remote,
                "repository": f"{self.org_name}/{repository.repository}",
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

    def __get_root_node_pkey(self, repository: Repository) -> Optional[str]:
        """
        Get the primary key of the root node from the vector db.
        """
        return f"{repository.remote}/{repository.repository}/-1"

    def __repository_to_nodes(self, repository: Repository) -> Node:
        """
        Given a repository, loads the entire repo into a tree. Doesn't compute any embeddings or summaries,
        just loads names and structure of node tree.

        Make sure to add the nodes to the self.treenode_cache.

        Args:
            repository (Repository): the repo to construct from.

        Returns:
            Node: root node of the tree
        """
        # Create root node for repository, OR use the node from the vector db if it exists.
        root_pkey = self.__get_root_node_pkey(repository)
        
        root = self.vector_db.get_code_page(root_pkey)
        if root is not None:
            return root

        root = Node(
            primary_key=root_pkey, # All root nodes have this pkey
            org_id=str(self.org_id),
            name=repository.repository,
            page_type=CodePageType.DIRECTORY,
            children_ids=[]
        )
        self.treenode_cache[root.data.primary_key] = root

        # Get repository contents from GitHub API
        repo_url = f"{GITHUB_API_BASE}/repositories/{repository.repository}/contents" # getting bad credentials error on this one.
        contents = requests.get(repo_url, headers=self.headers).json()
        contents.raise_for_status()

        
        # Recursively build tree
        def build_tree(parent_node: Node, items: list, path: str = ""):
            for item in items:
                item_path = f"{path}/{item['name']}" if path else item['name']
                node_id = f"{repository.remote}/{repository.repository}/{item_path}"
                
                # Create node for this item
                node = Node(
                    primary_key=node_id,
                    org_id=self.org_id,
                    name=item['name'],
                    page_type=CodePageType.DIRECTORY if item['type'] == 'dir' else CodePageType.FILE,
                    children_ids=[]
                )
                self.treenode_cache[node_id] = node
                parent_node.children_ids.append(node_id)

                # Recursively get contents if directory
                if item['type'] == 'dir':
                    subdir_url = f"{GITHUB_API_BASE}/repositories/{repository.repository}/contents/{item_path}"
                    subdir_response = requests.get(subdir_url, headers=self.headers)
                    subdir_response.raise_for_status()
                    build_tree(node, subdir_response.json(), item_path)

        # Build full tree starting from root
        build_tree(root, contents)
        
        return root

    def __index_tree(self, root: Node):
        """DFS iterates through the structure, and adds each page to the vector db.

        At each page, we generate a summary, and add the page to the vector db.
        At directories, we generate a summary given the child summaries.

        Args:
            root (Node): root node to traverse through
        """
        # 1. Index the current node.
        self.vector_db.add_code_page(root.data)

        if root.page_type == CodePageType.DIRECTORY:
            for node_id in root.children_ids:
                # 2. load the page for this id from the treenode cache. If the node doesn't exist in the cache, load it from the vector db.
                node = self.treenode_cache.get(node_id)
                if node is None:
                    node = self.vector_db.get_code_page(node_id)
                
                # 3. Traverse to each page, dfs style.
                self.__index_tree(node)

    def index_merkle(self, repository: Repository) -> bool:
        """
        Get a list of all the files in the repo, index each file with the vector DB
        """

        try:
            # 1. Get the entire file structure of the repo
            tree = self.__repository_to_nodes(repository)

            # 2. dfs through the structure, add each page to the vector DB.
            self.__index_tree(tree)
        except Exception as e:
            logging.error(f"Failed to query repositories: {str(e)}")
            return False

    async def index(self, repository: Repository) -> bool:
        """
        Index or reindex a repository for searching

        Args:
            repository: Repository to index

        Returns:
            bool indicating if indexing was successful
        """
        if INDEX_WITH_GREPTILE:
            return self.index_greptile(repository)
        else:
            return self.index_merkle(repository)

    def query_greptile(
        self, query: str, limit: int = 5
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        try:
            url = f"{self.api_base}/query"

            payload = {
                "messages": [{"id": "query", "content": query, "role": "user"}],
                "repositories": [
                    {
                        "remote": repo.remote,
                        "repository": repo.repository,
                        "branch": repo.branch,
                    }
                    for repo in self.repos
                ],
                "stream": False,
                "genius": True,
            }

            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            results = response.json()
            results_kbs = results["sources"][:limit]

            kbs = []
            for result in results_kbs:
                if "summary" not in result or "distance" not in result:
                    continue

                kbs.append(
                    KnowledgeBaseResponse(
                        content=result["summary"],
                        source="github",
                        relevance_score=result["distance"],
                    )
                )

            return kbs, results["message"]
        except Exception as e:
            logging.error(f"Failed to query repositories: {str(e)}")
            return [], ""

    def query_merkle(
        self, query: str, limit: int = 5
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """Queries the merkle tree based search engine.

        Args:
            query: Natural language query about the codebase
            limit: Maximum number of results to return

        Returns:
            Tuple of (List of KnowledgeBaseResponse objects containing search results,
                      String answer to the query)
        """
        # 1. Load in the entire tree for the codebase (unsure on how I'm going to do this. )
        # 2. Get the top k via vector db
        # 3. In the sysprompt, specify the codebase structure with just the present nodes, as well as the nodes that are provided, and the content in those nodes.
        # 4. Return some response to the user + those code pages. TODO Before you go barelling ahead into this, think about looing into graphRAG

    def query(
        self, query: str, limit: int = 5
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
        Search code repositories with natural language queries

        Args:
            query: Natural language query about the codebase
            limit: Maximum number of results to return

        Returns:
            Tuple of (List of KnowledgeBaseResponse objects containing search results,
                      String answer to the query)
        """
        if INDEX_WITH_GREPTILE:
            return self.query_greptile(query, limit)
        else:
            return self.query_merkle(query, limit)
