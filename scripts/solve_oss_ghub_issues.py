"""
A basic script that solves a few subsets of issues from some commercial oss projects.
"""

from uuid import UUID

from src.integrations.github import GithubIntegration, Repository
from src.integrations.issue_kb import IssueKnowledgeBase
from src.integrations.documentation_kb import DocumentationKnowledgeBase
from src.model.issue import Issue

MEM0AI_ORG_ID = UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1")

# Setup repo, issue, and documentation knowledge bases
def setup_repos(org_id: UUID, repo_name: str):
    github = GithubIntegration(org_id, repo_name)
    issue_kb = IssueKnowledgeBase(org_id)
    # doc_kb = DocumentationKnowledgeBase(org_id)

    # github.index(Repository(remote="github", repository=repo_name, branch="main"))
    
    issues = github.get_all_issues_json(repo_name, state=None)
    for issue in issues:
        issue_kb.index(Issue(
            primary_key=issue["id"], 
            problem_description=issue["title"], 
            comments=issue["body"]
        ))

    # doc_kb.index()

def solve_issue(repo: str, issue_id: int):
    """
    Solves a given issue from a given repository.
    """

    github = GithubIntegration(UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1"), "mem0ai")
    print(github.list_repositories())
