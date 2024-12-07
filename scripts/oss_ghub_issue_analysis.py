from uuid import UUID
import logging
from datetime import datetime
import json
from statistics import mean
from typing import Dict
from dotenv import load_dotenv
import csv

load_dotenv()

from src.integrations.kbs.github_kb import GithubIntegration
from src.storage.supa import SupaClient
from include.constants import TRIGGER_ORG_ID, LIGHT_DASH_ORG_ID

def analyze_github_issues(org_id: UUID) -> Dict:
    """
    Analyzes closed issues from a GitHub repository to calculate completion times.

    Args:
        repo_url: URL or org/repo string for the GitHub repository

    Returns:
        Dictionary containing issue completion times and average completion time
    """

    # Extract org/repo from URL if full URL provided
    data = SupaClient(org_id).get_user_data("org_name", "repo_name", debug=True)
    org_name = data["org_name"]
    repo_name = data["repo_name"]

    github = GithubIntegration(org_id, org_name)
    issues = github.get_all_issues_json(repo_name, state="closed", fetch_comments=False)

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
        "issue_completion_times_in_seconds": completion_times,
        "average_completion_time_in_seconds": avg_completion_time,
    }

def analyze_repos():
    # Example usage
    org_ids = []
    with open("include/cache/cached_user_data.json", "r") as f:
        data = json.load(f)
        for org_id, _ in data.items():
            org_ids.append(UUID(org_id))

    # Read existing entries if file exists
    existing_entries = set()
    try:
        with open("scripts/data/oss_ticket_stats.csv", "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                existing_entries.add(row[0])  # Store repo names
    except FileNotFoundError:
        # Create new file with header if it doesn't exist
        with open("scripts/data/oss_ticket_stats.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["repo", "average_completion_time", "total_completion_time"])

    # Append new entries
    with open("scripts/data/oss_ticket_stats.csv", "a") as f:
        writer = csv.writer(f)
        for org_id in org_ids:
            if org_id not in existing_entries:
                results = analyze_github_issues(org_id)
                
                logging.info(results)
                
                values_in_seconds = [
                    x.total_seconds() for x in results["issue_completion_times"].values()
                ]
                writer.writerow(
                    [
                        org_id,
                        results["average_completion_time"] / 3600,
                        sum(values_in_seconds) / 3600,
                    ]
                )