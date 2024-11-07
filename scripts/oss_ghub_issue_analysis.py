from uuid import UUID
from datetime import datetime
import os
from statistics import mean
from typing import Dict
from dotenv import load_dotenv
import csv

load_dotenv()

from src.integrations.kbs.github_kb import GithubIntegration


def analyze_github_issues(repo_url: str) -> Dict:
    """
    Analyzes closed issues from a GitHub repository to calculate completion times.

    Args:
        repo_url: URL or org/repo string for the GitHub repository

    Returns:
        Dictionary containing issue completion times and average completion time
    """

    # Extract org/repo from URL if full URL provided
    github = GithubIntegration(UUID("90a11a74-cfcf-4988-b97a-c4ab21edd0a1"), repo_url)
    issues = github.get_all_issues_json(repo_url)

    time_deltas = []
    completion_times = {}
    for issue in issues:
        if issue["closed_at"] and issue["created_at"]:
            # Parse datetime strings to datetime objects
            closed_at = datetime.strptime(issue["closed_at"], "%Y-%m-%dT%H:%M:%SZ")
            created_at = datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ")

            # Calculate time delta between creation and closing
            completion_time = closed_at - created_at
            completion_times[issue["number"]] = completion_time
            time_deltas.append(completion_time.total_seconds())

    # Calculate average completion time
    avg_completion_time = mean(time_deltas) if time_deltas else 0

    return {
        "issue_completion_times": completion_times,
        "average_completion_time": avg_completion_time,
    }


if __name__ == "__main__":
    # Example usage
    repos = [
        "mem0ai/mem0",
        "cpacker/MemGPT",
        "trypear/pearai-master",
        "milvus-io/milvus",
        "qdrant/qdrant",
        "langchain-ai/langchain",
        "run-llama/llama_index",
    ]

    with open("data/oss_ticket_stats.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["repo", "average_completion_time", "total_completion_time"])

        for repo in repos:
            results = analyze_github_issues(repo)
            values_in_seconds = [
                x.total_seconds() for x in results["issue_completion_times"].values()
            ]
            writer.writerow(
                [
                    repo,
                    results["average_completion_time"] / 3600,
                    sum(values_in_seconds) / 3600,
                ]
            )
