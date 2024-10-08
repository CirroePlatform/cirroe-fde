from pydantic import BaseModel
from . import base_action

from src.classifier import Classifier
from src.model.issue import Issue

class HandleIssueAction(base_action.BaseAction):
    """
    Handles inbound issue actions.
    """
    def __init__(self) -> None:
        self.classifier = Classifier()

    def handle_request(self, request_params: Issue) -> BaseModel:
        """
        Handles a request and returns the response.
        
        def handle_issue(issue):
            if (is_active_or_dangerous(issue)); then loop in engineer with humanlayer async

            category = categorize(issue)

            # This should allocate different knowledge bases depending on the 
            # availability of integrations, and the category type.
            comment, issue_action = handle_based_on_category(issue, category)

            add_comment_to_issue(issue, comment)

            # action refers to switching it to a different queue, closing 
            # it, raising severity, etc. any issue change.
            perform_action_on_issue(issue, issue_action)
        """
        issue = request_params

        # loop in humanlayer somehow for this entire statement
        if self.classifier.is_dangerous(issue):
            pass

        issue_type = self.classifier.get_type(issue)
