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
async def setup_repos(org_id: UUID, repo_name: str):
    github = GithubIntegration(org_id, repo_name)
    issue_kb = IssueKnowledgeBase(org_id)
    # doc_kb = DocumentationKnowledgeBase(org_id)

    # github.index(Repository(remote="github", repository=repo_name, branch="main"))
    
    issues = github.get_all_issues_json(repo_name, state=None)
    for issue in issues:
        
        comments = {} 
        for comment in issue["comments"]:
            comments[comment["user"]["login"]] = comment["body"]
        
        #  Issue id is not a uuid, need to co
        await issue_kb.index(Issue(
            primary_key=str(issue["id"]), 
            description=f"title: {issue['title']}, description: {issue['body']}", 
            comments=comments,
            org_id=MEM0AI_ORG_ID
        ))

    # doc_kb.index()

def solve_issue(repo: str, issue_id: int):
    """
    Solves a given issue from a given repository.
    """

    github = GithubIntegration(UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1"), "mem0ai")
    print(github.list_repositories())
