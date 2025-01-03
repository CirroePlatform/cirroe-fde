import os
import tqdm
import json
import traceback
import time
from uuid import UUID
import requests
import logging
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel
from bs4 import BeautifulSoup
from datetime import datetime

from src.integrations.cleaners.traceback_cleaner import TracebackCleaner
from src.integrations.kbs.base_kb import BaseKnowledgeBase, KnowledgeBaseResponse
from src.model.code import CodePage, CodePageType
from include.constants import INDEX_WITH_GREPTILE, GITHUB_API_BASE, GITFILES_CACHE_DIR
from src.model.issue import Issue, Comment
from src.model.news import News, NewsSource

from src.storage.vector import VectorDB


class Repository(BaseModel):
    remote: str  # e.g. "github.com"
    repository: str  # e.g. "username/repo"
    branch: str = "main"


class LinkGithubRequest(BaseModel):
    org_id: UUID
    org_name: str


class GithubKnowledgeBase(BaseKnowledgeBase):
    """
    Integration with Github repositories via Greptile API for code search and analysis.
    """

    def __init__(
        self,
        org_id: UUID,
        org_name: str,
        repos: Optional[List[Repository]] = None,
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

        self.greptile_headers = {
            "Authorization": f"Bearer {os.getenv('GREPTILE_API_KEY')}",
            "X-GitHub-Token": f"{self.gh_token}",
            "Content-Type": "application/json",
        }
        self.github_headers = {
            "Authorization": f"Bearer {self.gh_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.repos = repos
        self.vector_db = VectorDB(self.org_id)
        self.traceback_cleaner = TracebackCleaner(self.vector_db)

    def get_github_token(self, org_id: str) -> str:
        """
        Get the GitHub token for an organization from supabase vault.
        """
        # TODO
        return os.getenv("GITHUB_TEST_TOKEN")

    def get_github_trending_news(self) -> Dict[str, News]:
        """
        Get the GitHub trending news for an organization from supabase vault.
        """
        trending_news = {}
        GITHUB_URL = "https://github.com"

        try:
            url = f"{GITHUB_URL}/trending"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all repository articles
            for repo_article in soup.select('.Box article.Box-row')[:15]:
                # Extract repository info
                title = repo_article.select_one('.h3').text.strip()
                username, repo_name = [x.strip() for x in title.split('/')]
                relative_url = repo_article.select_one('.h3 a')['href']
                full_url = f"{GITHUB_URL}{relative_url}"

                # Get description
                description = repo_article.select_one('p.my-1')
                description = description.text.strip() if description else ''


                # Get readme content
                readme_response = requests.get(
                    f"https://api.github.com/repos{relative_url}/README.md",
                    headers={"Accept": "application/vnd.github.raw"}
                )

                if readme_response.status_code == 200:
                    repo_key = f"{username}/{repo_name}"
                    trending_news[repo_key] = News(
                        title=repo_key,
                        content=f"Description: {description}\nReadme: {readme_response.text}",
                        url=full_url,
                        source=NewsSource.GITHUB_TRENDING,
                        timestamp=datetime.now()
                    )

        except Exception as e:
            logging.error(f"Error crawling GitHub trending: {e}")
            
        return trending_news
    
    def json_issues_to_issues(self, issues: List[Dict]) -> List[Issue]:
        """
        Convert a list of JSON issues to a list of Issue objects

        Args:
            issues (List[Dict]): List of JSON issues

        Returns:
            List[Issue]: List of Issue objects
        """
        issue_list = []

        for issue in issues:
            try:
                comments = []
                if "comments" in issue:
                    for comment in issue["comments"]:
                        comments.append(
                            Comment(
                                requestor_name=comment["user"]["login"],
                                comment=comment["body"],
                            )
                        )

                issue_list.append(
                    Issue(
                        primary_key=str(issue["id"]),
                        description=f"title: {issue['title']}, description: {issue['body']}",
                        comments=comments,
                        org_id=self.org_id,
                        ticket_number=str(issue["number"]),
                    )
                )
            except Exception as e:
                logging.error(f"Failed to process issue: {e}")
                continue

        return issue_list

    def get_all_issues_json(
        self,
        repo_name: str,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
        fetch_comments: bool = True,
        include_prs: bool = False,
    ) -> Dict[str, Any]:
        """
        Get all issues (excluding pull requests) for some provided repository.

        Args:
            repo_name: Name of repository to fetch issues from
            state: Optional filter for issue state (open, closed)
            labels: Optional list of label names to filter issues by
            fetch_comments: Whether to fetch comments for each issue
            include_prs: Whether to include pull requests in the response
        """
        if "github.com" in repo_name:
            repo_name = "/".join(repo_name.split("/")[-2:])
        else:
            repo_name = repo_name

        # Add parameters to exclude pull requests and filter by state and labels
        params = {"per_page": 100, "page": 1}
        if state is not None:
            params["state"] = state

        url = f"{GITHUB_API_BASE}/repos/{self.org_name}/{repo_name}/issues"

        all_issues = []
        while True:
            try:
                response = requests.get(url, headers=self.github_headers, params=params)
                response.raise_for_status()
                content = response.json()
            except (
                requests.exceptions.HTTPError,
                requests.exceptions.RequestException,
            ) as e:
                if response.status_code == 403:
                    logging.warning(f"Received 403 Forbidden response for {url}")
                else:
                    logging.warning(f"Request failed for {url}: {str(e)}")
                content = []

            # Filter out pull requests from the response
            issues = [
                issue for issue in content if include_prs or "pull_request" not in issue
            ]
            final_issues = []

            # Fetch comments for each issue
            for i in tqdm.tqdm(
                range(len(issues)),
                desc=f"Fetching comments and/or labels for {len(issues)} issues",
            ):

                # Get labels if they exist, and remove this from the set if it doesn't satisfy label constraints
                issue_number = issues[i]["number"]
                comments_url = issues[i]["comments_url"]
                if fetch_comments:
                    try:
                        comments_response = requests.get(
                            comments_url, headers=self.github_headers
                        )
                        comments_response.raise_for_status()

                        # Add comments to the issue object
                        issues[i]["comments"] = comments_response.json()
                    except (
                        requests.exceptions.Timeout,
                        requests.exceptions.ReadTimeout,
                        requests.exceptions.ConnectTimeout,
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

                    for _ in range(3):
                        try:
                            issue_labels = set(self.get_labels(issue_number, url))
                            break
                        except Exception as e:
                            logging.error(
                                f"Failed to get labels for issue {issue_number}: {str(e)}. Sleeping for 10 seconds."
                            )
                            logging.error(traceback.format_exc())
                            time.sleep(10)

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

    def get_labels(self, issue_number: int, base_url: str) -> List[str]:
        """
        Get the labels for an issue.

        Accepts a base url to the issues endpoint (e.g. https://api.github.com/repos/{org_name}/{repo_name}/issues), and the issue number.
        """
        label_url = f"{base_url}/{issue_number}/labels"
        label_response = requests.get(label_url, headers=self.github_headers)
        label_response.raise_for_status()

        return [label["name"] for label in label_response.json()]

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
        url = f"{GITHUB_API_BASE}/orgs/{self.org_name}/repos"

        page = 1
        repos = []
        while True:
            response = requests.get(
                url, headers=self.github_headers, params={"per_page": 100, "page": page}
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
            response = requests.get(url, headers=self.github_headers)

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

    def get_files(self, repository: str) -> List[CodePage]:
        """
        Get a list of all the files' contents in the repo by recursively fetching from GitHub API

        Args:
            repository: Repository name

        Returns:
            List of CodePage objects containing file contents and metadata
        """
        code_pages = []

        # 1. Get all the files in the repo from cache if already exists
        if os.path.exists(f"{GITFILES_CACHE_DIR}/{repository}"):
            with open(f"{GITFILES_CACHE_DIR}/{repository}", "r") as f:
                code_json = json.load(f)
                code_pages = [
                    CodePage(**code_page) for code_page in code_json["code_pages"]
                ]
            return code_pages
        logging.info(f"Fetching and indexing contents for {repository}")

        def fetch_contents(path: str = ""):
            url = (
                f"{GITHUB_API_BASE}/repos/{self.org_name}/{repository}/contents/{path}"
            )
            response = requests.get(url, headers=self.github_headers)
            response.raise_for_status()

            contents = response.json()

            # Handle both single file and directory responses
            if not isinstance(contents, list):
                contents = [contents]

            for item in contents:
                if item["type"] == "file":
                    # If file is non-text data, skip it
                    if (
                        item["name"]
                        .lower()
                        .endswith(
                            (
                                ".png",
                                ".jpg",
                                ".jpeg",
                                ".gif",
                                ".bmp",
                                ".tiff",
                                ".ico",
                                ".webp",
                            )
                        )
                    ):
                        continue

                    # Get raw file content
                    content_response = requests.get(
                        item["download_url"], headers=self.github_headers
                    )
                    content_response.raise_for_status()

                    code_pages.append(
                        CodePage(
                            primary_key=item["path"],
                            content=content_response.text,
                            org_id=str(self.org_id),
                            page_type=CodePageType.CODE,
                            sha=item["sha"],
                        )
                    )
                    logging.info(f"Fetched code file: {item['path']}")

                elif item["type"] == "dir":
                    # TODO switch to postorder traversal, add AI summaries, can do merkle tree of the files.
                    fetch_contents(item["path"])

        try:
            fetch_contents()

            # Cache the files for future use
            os.makedirs(GITFILES_CACHE_DIR, exist_ok=True)
            with open(f"{GITFILES_CACHE_DIR}/{repository}", "w") as f:
                code_json = {
                    "code_pages": [code_page.model_dump() for code_page in code_pages]
                }
                json.dump(code_json, f)

            return code_pages

        except Exception as e:
            logging.error(f"Failed to fetch repository contents: {str(e)}")
            logging.error(traceback.format_exc())
            return []

    def index_custom(self, repository: Repository) -> bool:
        """
        Get a list of all the files in the repo, index each file with the vector DB
        """

        try:
            # 1. Get all the files in the repo
            files = self.get_files(repository.repository)

            # 2. Add each file to the vector db
            for file in tqdm.tqdm(files, desc=f"Indexing code files for {repository}"):
                self.vector_db.add_code_file(file)

            return True
        except Exception as e:
            logging.error(f"Failed to index repository: {str(e)}")
            logging.error(traceback.format_exc())
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
            return self.index_custom(repository)

    def __query_greptile(
        self, query: str, limit: int = 5
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
        Query the Greptile API for code search

        Args:
            query (str): Natural language query about the codebase
            limit (int, optional): Maximum number of results to return. Defaults to 5.

        Returns:
            Tuple[List[KnowledgeBaseResponse], str]: List of KnowledgeBaseResponse objects containing search results,
                      String answer to the query
        """
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

    def __query_custom(
        self, query: str, limit: int = 5, tb: Optional[str] = None
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
        Query the vector db for code search

        Args:
            query (str): Natural language query about the codebase
            limit (int, optional): Maximum number of results to return

        Returns:
            Tuple[List[KnowledgeBaseResponse], str]: List of KnowledgeBaseResponse objects containing search results,
                      String answer to the query
        """
        try:
            query_vector = self.vector_db.vanilla_embed(query)
            results = self.vector_db.get_top_k_code(limit, query_vector)

            response = "<code_pages>"
            for result in results.values():
                code_page = CodePage(**json.loads(result["metadata"]))
                similarity = result["similarity"]

                response += f"<code_page_{code_page.primary_key}_similarity>{similarity}</code_page_{code_page.primary_key}_similarity>"
                response += f"<code_page_{code_page.primary_key}_content>{code_page.content}</code_page_{code_page.primary_key}_content>"

            if tb is not None:
                cleaned_results = self.traceback_cleaner.clean(tb)
                response += f"{json.dumps([step.model_dump() for step in cleaned_results])}"  # TODO not sure if we should surround this with tags? also untested rn.

            response += "</code_pages>"
            return [], response

        except Exception as e:
            logging.error(f"Failed to query documentation: {str(e)}")
            logging.error(traceback.format_exc())
            return [], str(e)

    def query(
        self, query: str, limit: int = 5, tb: Optional[str] = None, **kwargs
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
            return self.__query_greptile(query, limit)
        else:
            return self.__query_custom(query, limit, tb)
