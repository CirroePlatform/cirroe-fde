from pydantic import BaseModel
from uuid import UUID

class GetLinkTokenRequest(BaseModel):
    uid: UUID
    org_name: str
    email: str
