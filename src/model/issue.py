from pydantic import BaseModel, HttpUrl, EmailStr, UUID4
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime
from discord.message import Attachment

class Comment(BaseModel):
    requestor_name: str
    comment: str


class DiscordMessage(BaseModel):
    content: str
    author: str
    attachments: List[Tuple[str, str]] = [] # [(url, media_type)]


class Issue(BaseModel):
    """
    Model for a customer issue, could be issue, slack thread, etc.
    """

    primary_key: str
    org_id: UUID
    vector: Optional[List[float]] = None
    description: str
    comments: List[Comment]  # a list of comments, sorted by earliest comment first
    ticket_number: Optional[str] = None


# Merge models
class Hook(BaseModel):
    id: UUID4
    event: str
    target: HttpUrl


class LinkedAccount(BaseModel):
    id: UUID4
    integration: str
    integration_slug: str
    category: str
    end_user_origin_id: Optional[str]
    end_user_organization_name: str
    end_user_email_address: EmailStr
    status: str
    webhook_listener_url: HttpUrl
    is_duplicate: Optional[bool]
    account_type: str


class EndUser(BaseModel):
    id: Optional[str]
    origin_id: Optional[str]
    organization_name: str
    organization_logo: Optional[str]
    email_address: EmailStr


class Data(BaseModel):
    id: str
    status: str
    error_description: Optional[str]
    end_user: EndUser
    first_incident_time: datetime
    last_incident_time: datetime
    is_muted: bool
    error_details: List[str]
    account_token: str


class WebhookPayload(BaseModel):
    hook: Hook
    linked_account: LinkedAccount
    data: Data


class OpenIssueRequest(BaseModel):
    requestor_id: UUID
    issue: Issue


class IndexAllIssuesRequest(BaseModel):
    org_id: UUID
