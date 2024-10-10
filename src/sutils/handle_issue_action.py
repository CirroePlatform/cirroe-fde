from pydantic import BaseModel
from . import base_action
from uuid import UUID

from src.model.issue import Issue

class HandleIssueAction(base_action.BaseAction):
    """
    Handles inbound issue actions for one particular user.
    """

    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        self.rb_client = None # fetch based on user
        self.rb_executor = None # fetch based on user

    def handle_request(self, request_params: Issue) -> BaseModel:
        """
        Handles a single request from fastapi frontend.
        """
        # 1. Find runbook for issue. Need to do classification here.
        # runbook = self.rb_client.get_runbook_for_issue(issue.problem_description)

        # 2. if runbook exists, call the runbook executor to run the book.
        # response = self.rb_client.run_book(runbook)

        # 3. If dne, alert some person with the correct background to handle the issue.
        # if response is None:
        #   humanlayerclient.alert_operator()

        # return response
