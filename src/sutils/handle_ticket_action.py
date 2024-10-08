from pydantic import BaseModel
from . import base_action

from src.classifier import Classifier
from src.model.ticket import Issue

class HandleTicketAction(base_action.BaseAction):
    """
    All server action wrappers
    """
    def __init__(self) -> None:
        self.classifier = Classifier()

    def handle_request(self, request_params: Issue) -> BaseModel:
        """
        Handles a request and returns the response.
        
        def handle_ticket(ticket):
            if (is_active_or_dangerous(ticket)); then loop in engineer with humanlayer async

            category = categorize(ticket)

            # This should allocate different knowledge bases depending on the 
            # availability of integrations, and the category type.
            comment, ticket_action = handle_based_on_category(ticket, category)

            add_comment_to_ticket(ticket, comment)

            # action refers to switching it to a different queue, closing 
            # it, raising severity, etc. any ticket change.
            perform_action_on_ticket(ticket, ticket_action)
        """
        issue = request_params

        # loop in humanlayer somehow for this entire statement
        if self.classifier.is_dangerous(issue):
            pass

        issue_type = self.classifier.get_type(issue)
