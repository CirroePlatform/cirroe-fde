from pydantic import BaseModel
from abc import ABC

class BaseAction(ABC):
    """
    All server action wrappers
    """
    def __init__(self) -> None:
        pass

    def handle_request(self, request_params: BaseModel) -> BaseModel:
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
        pass
