from pydantic import BaseModel, HttpUrl, EmailStr, UUID4
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime

class Issue(BaseModel):
    """
    Model for a customer issue, could be issue, slack thread, etc.
    """

    tid: UUID
    problem_description: str
    comments: List[Tuple[str, str]] # a list of (requestor_name, comment) objects

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
    requestor: str
    issue: Issue
