from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel
from uuid import UUID


class KnowledgeBaseResponse(BaseModel):
    """Response model for knowledge base queries"""

    source: str  # Source of the information (e.g. "github", "cloud", "issue")
    content: str  # The relevant content
    relevance_score: float  # How relevant this piece of information is to the query
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata like timestamps, urls, etc


class BaseKnowledgeBase(ABC):
    """
    Abstract base class for knowledge base integrations.
    Provides interface for indexing and querying data sources.
    """

    def __init__(self, org_id: UUID):
        """
        Initialize knowledge base for an organization

        Args:
            org_id: Organization ID to scope the knowledge base
        """
        self.org_id = org_id

    @abstractmethod
    async def index(self, data: Any) -> bool:
        """
        Index new data into the knowledge base

        Args:
            data: Data to be indexed. Format depends on specific implementation

        Returns:
            bool: True if indexing was successful
        """
        pass

    @abstractmethod
    def query(self, query: str, limit: int = 5) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
        Query the knowledge base for relevant information

        Args:
            query: Natural language query string
            limit: Maximum number of results to return

        Returns:
            Tuple of (List of KnowledgeBaseResponse objects containing relevant information,
                      String answer to the query)
        """
        pass

    def get_tool_description(self) -> str:
        """
        Get description of this knowledge base for use as a tool

        Returns:
            String describing the knowledge base's capabilities
        """
        return f"""Use this tool to search the {self.__class__.__name__} for information relevant to debugging issues.
        The knowledge base contains indexed data from {self.__class__.__name__}.
        Provide a natural language query describing what information you're looking for."""
