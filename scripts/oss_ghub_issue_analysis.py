from uuid import UUID
import uuid
import tqdm
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
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
from include.constants import MINDEE_ORG_ID, UNSLOTH_ORG_ID, UEBERDOSIS_ORG_ID


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
    # Get current time and calculate cutoff date (3 months ago)
    now = datetime.now()
    three_months_ago = datetime(
        now.year, now.month - 3 if now.month > 3 else now.month + 9, now.day
    )

    for issue in issues:
        if issue["closed_at"] and issue["created_at"]:
            # Parse datetime strings to datetime objects
            closed_at = datetime.strptime(issue["closed_at"], "%Y-%m-%dT%H:%M:%SZ")
            created_at = datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ")

            # Only consider issues from last 3 months
            if created_at >= three_months_ago:
                # Calculate time delta between creation and closing
                completion_time = (closed_at - created_at).total_seconds()
                completion_times[issue["number"]] = completion_time
                time_deltas.append(completion_time)

    # Calculate average completion time
    avg_completion_time = mean(time_deltas) if time_deltas else 0
    # Calculate median completion time
    median_completion_time = (
        sorted(time_deltas)[len(time_deltas) // 2] if time_deltas else 0
    )

    return {
        "issue_completion_times_in_seconds": completion_times,
        "average_completion_time_in_seconds": avg_completion_time,
        "median_completion_time_in_seconds": median_completion_time,
    }


def analyze_repos():
    # Example usage
    org_ids = []
    with open("include/cache/cached_user_data.json", "r") as f:
        data = json.load(f)
        for org_id, org_data in data.items():
            name = org_data["org_name"]
            org_ids.append((UUID(org_id), name))

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
            writer.writerow(
                [
                    "repo",
                    "average_completion_time",
                    "total_completion_time",
                    "median_completion_time",
                ]
            )

    # Append new entries
    with open("scripts/data/oss_ticket_stats.csv", "a") as f:
        writer = csv.writer(f)
        for org_id, org_name in org_ids:
            if org_name not in existing_entries:
                logging.info(f"Analyzing {org_name}")
                results = analyze_github_issues(org_id)
                writer.writerow(
                    [
                        org_name,
                        results["average_completion_time_in_seconds"] / 3600,
                        sum(results["issue_completion_times_in_seconds"].values())
                        / 3600,
                        results["median_completion_time_in_seconds"] / 3600,
                    ]
                )


def extract_github_links(url):
    """
    Scrape a website and extract GitHub links from the page.

    Args:
        url (str): The landing page URL to scrape

    Returns:
        dict: A dictionary with the original website as key and GitHub link as value
    """
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        # Fetch the webpage content
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Patterns to identify GitHub links
        github_patterns = [
            r"https?://(?:www\.)?github\.com/[a-zA-Z0-9-]+(?:/[a-zA-Z0-9-]+)?",
            r"github\.com/[a-zA-Z0-9-]+(?:/[a-zA-Z0-9-]+)?",
        ]

        # Searches for GitHub links in different parts of the page
        github_links = set()

        # Search in all anchor tags
        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Normalize the URL
            full_url = urljoin(url, href)

            # Check if the link matches GitHub patterns
            for pattern in github_patterns:
                match = re.search(pattern, full_url, re.IGNORECASE)
                if match:
                    # Ensure it's a clean GitHub URL
                    github_link = match.group(0)
                    if not github_link.startswith(("http://", "https://")):
                        github_link = f"https://{github_link}"
                    github_links.add(github_link)

        # Return results
        return {url: list(github_links)[0]} if github_links else {}

    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return {}


def bulk_extract_github_links(websites):
    """
    Extract GitHub links for multiple websites, and return a dictionary of website to GitHub link mappings.

    Args:
        websites (list): List of website URLs to scrape

    Returns:
        dict: Dictionary of website to GitHub link mappings
    """
    results = {}
    for site in tqdm.tqdm(websites, desc="Extracting GitHub links"):
        github_link = extract_github_links(site)
        results.update(github_link)

    cache_data_new_entries = {}
    for site, link in tqdm.tqdm(results.items(), desc="Creating new cache entries"):
        org_id = str(uuid.uuid4())
        org_name = site.split("/")[-2]
        repo_name = link.split("/")[-1]

        cache_data_new_entries[org_id] = {
            "repo_url": link,
            "org_name": org_name,
            "repo_name": repo_name,
        }

    with open("include/cache/cached_user_data.json", "r") as f:
        data = json.load(f)
        data.update(cache_data_new_entries)

    with open("include/cache/cached_user_data.json", "w") as f:
        json.dump(data, f)
