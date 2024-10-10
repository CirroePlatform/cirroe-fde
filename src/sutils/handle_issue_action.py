from pydantic import BaseModel
from . import base_action
from typing import Tuple, Union

from src.classifier import Classifier
from src.model.issue import Issue, IssueType

class HandleIssueAction(base_action.BaseAction):
    """
    Handles inbound issue actions.
    """
    def __init__(self) -> None:
        self.classifier = Classifier()

    def handle_request(self, request_params: Issue) -> BaseModel:
        """
        
        """
        # 1. Find runbook for issue
        # 2. if runbook exists, call the runbook executor to run the book.
        # 3. If dne, alert some person with the correct background to handle the issue.