"""
Merge API integration functionality.
"""

from uuid import UUID
import requests
from merge.client import Merge
from merge.resources.ticketing import CommentRequest
from dotenv import load_dotenv
import os
from typing import Optional

from src.model.auth import GetLinkTokenRequest, GetAccountTokenRequest
from src.storage.supa import SupaClient

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
        "end_user_origin_id": user.uid,  # unique entity ID
        "end_user_organization_name": user.org_name,  # your user's organization name
        "end_user_email_address": user.email,  # your user's email address
        "categories": ["ticketing"],  # choose your category
    }

    headers = {"Authorization": f"Bearer {api_key}"}

    link_token_result = requests.post(
        LINK_TOKEN_URL, data=body, headers=headers, timeout=10
    )
    print(f"link token response: {link_token_result}")
    link_token = link_token_result.json().get("link_token")
    # integration_name = link_token_result.json().get("integration_name") # TODO might need this to categorize different integrations.

    return link_token


def retrieve_account_token(
    public_token_req: GetAccountTokenRequest, api_key: str = API_KEY
) -> str:
    """
    Get an account token provided with the short term public token. Sets value in db.
    """
    headers = {"Authorization": f"Bearer {api_key}"}

    account_token_url = (
        "https://api.merge.dev/api/integrations/account-token/{}".format(
            public_token_req.public_token
        )
    )
    account_token_result = requests.get(account_token_url, headers=headers)
    print(f"account response: {account_token_result}")

    account_token = account_token_result.json().get("account_token")

    dbclient = SupaClient(public_token_req.uid)
    dbclient.set_user_data(account_token=account_token)

    return account_token


def get_comments_from_ticket(tid: UUID):
    """
    Get all comments from a ticket
    """
    client.ticketing.comments.retrieve(tid)


def add_comment_to_ticket(tid: UUID, message: str, msg_html: Optional[str] = None):
    """
    Get all comments from a ticket
    """
    client.ticketing.comments.create(
        model=CommentRequest(
            ticket=tid,
            body="When will these integrations be done? You all should use Merge.",
            html_body="When will these integrations be done? You all should use <b>Merge<b>.",
        ),
    )
