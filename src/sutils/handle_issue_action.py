from pydantic import BaseModel
from . import base_action
from uuid import UUID

from src.model.issue import Issue

from src.runbook import RunBookExecutor

class HandleIssueAction(base_action.BaseAction):
    """
    Handles inbound issue actions for one particular user.
    """

    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        self.db_client = None # fetch based on user
        self.rb_executor = RunBookExecutor()

    def handle_request(self, request_params: Issue) -> BaseModel:
        """
        Handles a single request from fastapi frontend.
        """
        # 1. Find runbook for issue.
        # top_k_similar_runbooks = self.db_client.get_top_k(issue.problem_description)
        top_k_similar_runbooks = []
        runbook = self.rb_executor.get_runbook_for_issue(request_params, top_k_similar_runbooks)

        # 2. if runbook exists, call the runbook executor to run the book.
        response = self.rb_executor.run_book(runbook)

        # 3. If dne, alert some person with the correct background to handle the issue.
        if response is None:
            return "Couldn't run book"
            # humanlayerclient.alert_operator()

        return response
