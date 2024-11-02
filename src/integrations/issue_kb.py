import json
from typing import Any, Dict, List
from uuid import UUID
from merge.resources.ticketing import Ticket
from merge.resources.ticketing.types import TicketStatusEnum
from src.model.issue import Issue
from src.integrations.base_kb import BaseKnowledgeBase, KnowledgeBaseResponse
from src.integrations.merge import client as merge_client

from src.storage.vector import VectorDB

from logger import logger

class IssueKnowledgeBase(BaseKnowledgeBase):
    """
    Knowledge base for searching and indexing historical support tickets/issues.
    Handles both Merge.dev API tickets and Issue model representations.
    """

    def __init__(self, org_id: UUID):
        """
        Initialize issue knowledge base for an organization
        
        Args:
            org_id: Organization ID to scope the knowledge base
        """
        super().__init__(org_id)
        self.vector_db = VectorDB(org_id)
        self.indexed_issues: Dict[str, Issue] = {}

    async def index(self, data: Any = None) -> bool:
        """
        Index tickets from either Merge API or Issue model representation
        
        Args:
            data: Optional specific Issue or Ticket to index, if None indexes all Merge tickets
            
        Returns:
            bool indicating if indexing was successful
        """
        try:
            # If specific ticket provided, just index that one
            if data:
                if isinstance(data, Ticket):
                    self._index_ticket(data)
                elif hasattr(data, 'tid'):  # Issue model
                    self.vector_db.add_issue(data)
                return True

            # Otherwise index all Merge tickets
            tickets = merge_client.ticketing.tickets.list()
            for ticket in tickets:
                self._index_ticket(ticket)
            
            return True

        except Exception as e:
            logger.error(f"Failed to index issues: {str(e)}")
            return False

    def _index_ticket(self, ticket: Ticket):
        """Helper to index a ticket from Merge API"""
        # Get comments for the ticket
        comments = merge_client.ticketing.comments.list(ticket_id=ticket.id)
        comment_texts = [c.body for c in comments]

        # Store indexed ticket data
        self.indexed_issues[str(ticket.id)] = {
            "title": ticket.name,
            "description": ticket.description,
            "status": ticket.status,
            "comments": comment_texts,
            "priority": ticket.priority,
            "created_at": ticket.created_at
        }

    async def query(self, query: str, limit: int = 5) -> List[KnowledgeBaseResponse]:
        """
        Search indexed tickets for relevant matches
        
        Args:
            query: Natural language query about previous issues
            limit: Maximum number of results to return
            
        Returns:
            List of KnowledgeBaseResponse objects containing relevant tickets
        """
        try:
            query_vector = self.vector_db.vanilla_embed(query)

            issues = self.vector_db.get_top_k_issues(limit, query_vector)

            results = []
            for issue_id, issue_data in issues.items():
                # source: str  # Source of the information (e.g. "github", "cloud", "issue")
                # content: str  # The relevant content
                # metadata: Dict[str, Any]  # Additional metadata like timestamps, urls, etc
                # relevance_score: float  # How relevant this piece of information is to the query

                results.append(KnowledgeBaseResponse(
                    content=issue_data["metadata"],
                    metadata=json.loads(issue_data["metadata"]),
                    source=f"Ticket #{issue_id}",
                    relevance_score=issue_data["similarity"]
                ))

            return results

        except Exception as e:
            logger.error(f"Failed to query issues: {str(e)}")
            return []