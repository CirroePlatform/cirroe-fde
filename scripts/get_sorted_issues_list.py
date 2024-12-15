from typing import List
from uuid import UUID
from src.integrations.kbs.github_kb import GithubKnowledgeBase


def get_sorted_issues_list(org_id: UUID) -> List[dict]:
    """
    Gets all open issues from GitHub and sorts them based on urgency and number of people waiting.

    Args:
        org_id (UUID): Organization ID to query issues for

    Returns:
        List[dict]: Sorted list of issues with priority scores
    """
    # Initialize GitHub KB
    github_kb = GithubKnowledgeBase(org_id)

    # Get all open issues
    issues_response, _ = github_kb.query("is:open", limit=100)

    # Process and score each issue
    scored_issues = []
    for issue in issues_response:
        # Calculate priority score based on:
        # - Number of comments (people waiting/discussing)
        # - Labels indicating urgency
        # - Age of issue
        priority_score = 0

        # Parse issue data
        issue_data = issue.metadata

        # Add score for number of comments
        priority_score += issue_data.get("comments", 0) * 2

        # Check labels for urgency indicators
        labels = issue_data.get("labels", [])
        for label in labels:
            label_name = label.lower()
            if "urgent" in label_name or "high-priority" in label_name:
                priority_score += 10
            elif "bug" in label_name:
                priority_score += 5

        scored_issues.append({"issue": issue_data, "priority_score": priority_score})

    # Sort issues by priority score (highest first)
    sorted_issues = sorted(
        scored_issues, key=lambda x: x["priority_score"], reverse=True
    )

    return sorted_issues
