from pydantic import BaseModel
from typing import List

class Step(BaseModel):
    sid: int
    description: str
    allowed_cmds: List[str]

class Runbook(BaseModel):
    rid: int
    steps: List[Step]
