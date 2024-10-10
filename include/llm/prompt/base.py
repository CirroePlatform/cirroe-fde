from abc import ABC, abstractmethod
from include.llm.client import base as llm


class Prompter(ABC):
    """
    A base class for different prompting techniques. Takes LLM
    client as an argument and provides a common interface to all the prompting classes.
    """

    def __init__(self, client: llm.AbstractLLM) -> None:
        self._client = client

    @abstractmethod
    def prompt(self, prompt: str) -> str:
        """
        The abstract method for a prompter to execute a prompt
        """
        pass
