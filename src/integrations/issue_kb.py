import os
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
        self.vector_db = VectorDB()
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
            results = []
            
            # Basic keyword matching for now
            # TODO: Add proper vector similarity search
            query_terms = query.lower().split()

            # update indexed issues with issues from vector db
            issues = self.vector_db.get_all_issues()
            self.indexed_issues.update({str(issue.tid): issue for issue in issues})
            
            for ticket_id, ticket_data in self.indexed_issues.items():
                score = 0
                searchable_text = [ticket_data['description']] + ticket_data['comments']
                if ticket_data['title']:
                    searchable_text.append(ticket_data['title'])
                text = ' '.join(searchable_text).lower()
                
                for term in query_terms:
                    if term in text:
                        score += 1
                
                if score > 0:
                    content = f"""Description: {ticket_data['description']}"""
                    if ticket_data['title']:
                        content = f"""Title: {ticket_data['title']}\n{content}"""
                    if ticket_data['status']:
                        content += f"\nStatus: {ticket_data['status']}"
                    if ticket_data['priority']:
                        content += f"\nPriority: {ticket_data['priority']}"
                    content += f"\nComments: {' | '.join(ticket_data['comments'])}"

                    results.append(
                        KnowledgeBaseResponse(
                            content=content,
                            source=f"Ticket #{ticket_id}",
                            score=score/len(query_terms)
                        )
                    )
            
            # Sort by score and limit results
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Failed to query issues: {str(e)}")
            return []