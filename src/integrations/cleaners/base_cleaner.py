from abc import ABC, abstractmethod


class BaseCleaner(ABC):
    @abstractmethod
    def clean(self, content: str) -> str:
        pass
