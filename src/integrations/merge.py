"""
Merge API integration functionality.
"""
import requests
from merge.client import Merge
from dotenv import load_dotenv
import os

from src.model.auth import GetLinkTokenRequest

load_dotenv()

API_KEY = os.environ.get("MERGE_ACCESS_KEY")
LINK_TOKEN_URL = "https://api.merge.dev/api/integrations/create-link-token"

client = Merge(api_key=API_KEY, account_token=os.environ.get("JIRA_TEST_TOKEN"))

# Replace api_key with your Merge production API Key
def create_link_token(user: GetLinkTokenRequest, api_key: str = API_KEY) -> str:
    """
    Create and return a link token for a users' integration.
    """
    body = {
        "end_user_origin_id": user.uid, # unique entity ID
        "end_user_organization_name": user.org_name,  # your user's organization name
        "end_user_email_address": user.email, # your user's email address
        "categories": ["ticketing"], # choose your category
    }

    headers = {"Authorization": f"Bearer {api_key}"}

    link_token_result = requests.post(LINK_TOKEN_URL, data=body, headers=headers, timeout=10)
    link_token = link_token_result.json().get("link_token")
    # integration_name = link_token_result.json().get("integration_name") # TODO might need this to categorize different integrations.

    return link_token

def retrieve_account_token(public_token: str, api_key: str = API_KEY) -> str:
    """
    Get an account token provided with the short term public token.
    """
    headers = {"Authorization": f"Bearer {api_key}"}

    account_token_url = "https://api.merge.dev/api/integrations/account-token/{}".format(public_token)
    account_token_result = requests.get(account_token_url, headers=headers)

    account_token = account_token_result.json().get("account_token")
    return account_token  # Save this in your database
