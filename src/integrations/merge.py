"""
Merge API integration class. 

Should be used to process inbound tickets, 
"""

import merge
from merge.client import Merge
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.environ.get("MERGE_ACCESS_KEY")
LINK_TOKEN_URL = "https://api.merge.dev/api/integrations/create-link-token"

client = Merge(api_key=API_KEY, account_token=os.environ.get("JIRA_TEST_TOKEN"))

import requests

# Replace api_key with your Merge production API Key
def create_link_token(user, api_key: str = API_KEY) -> str:
    """
    Create and return a link token for a users' integration.
    """
    body = {
        "end_user_origin_id": user.organization.id, # unique entity ID
        "end_user_organization_name": user.organization.name,  # your user's organization name
        "end_user_email_address": user.email_address, # your user's email address
        "categories": ["hris", "ats", "accounting", "ticketing", "crm"], # choose your category
    }

    headers = {"Authorization": f"Bearer {api_key}"}

    link_token_result = requests.post(LINK_TOKEN_URL, data=body, headers=headers, timeout=10)
    link_token = link_token_result.json().get("link_token")
    # integration_name = link_token_result.json().get("integration_name") # TODO might need this to categorize different integrations.

    return link_token
