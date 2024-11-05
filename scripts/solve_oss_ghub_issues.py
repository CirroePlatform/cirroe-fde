"""
A basic script that solves a few subsets of issues from some commercial oss projects.
"""

from typing import List
import requests

from src.core.tools import SearchTools

def solve_issues(repo: str, issue_ids: List[int]):
    """
    Solves a given number of issues from a given repository and issue type.
    """

    for issue_id in issue_ids:
        issue_data = requests.get(f"https://api.github.com/repos/{repo}/issues/{issue_id}").json()
        print(issue_data)