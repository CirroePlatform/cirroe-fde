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
        """
        pass
