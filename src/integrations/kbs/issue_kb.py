from src.integrations.kbs.base_kb import BaseKnowledgeBase, KnowledgeBaseResponse
from typing import List, Tuple, Optional
from src.storage.vector import VectorDB
from src.model.issue import Issue
from anthropic import Anthropic
from logger import logger
from uuid import UUID
import traceback
import json


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
        self.client = Anthropic()

    async def index(self, data: Issue = None) -> bool:
        """
        Index a ticket from either Merge API or Issue model representation

        Args:
            data: Optional specific Issue or Ticket to index, if None indexes all Merge tickets

        Returns:
            bool indicating if indexing was successful
        """
        try:
            # If specific ticket provided, just index that one
            if data:
                self.vector_db.add_issue(data)

            return True

        except Exception as e:
            logger.error(f"Failed to index issues: {str(e)}")
            return False

    def query(
        self, query: str, limit: int = 5, tb: Optional[str] = None, **kwargs
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
        Search indexed tickets for relevant matches

        Args:
            query: Natural language query about previous issues
            limit: Maximum number of results to return

        Returns:
            Tuple of (List of KnowledgeBaseResponse objects containing relevant tickets,
                      String answer to the query)
        """
        try:
            query_vector = self.vector_db.vanilla_embed(query)
            issues = self.vector_db.get_top_k_issues(limit, query_vector)
            response = "<issues>"
            for result in issues.values():
                issue = Issue(**json.loads(result["metadata"]))
                similarity = result["similarity"]

                response += f"<issue_{issue.ticket_number}_similarity>{similarity}</issue_{issue.ticket_number}_similarity>"
                response += f"<issue_{issue.ticket_number}_content>{issue.description}</issue_{issue.ticket_number}_content>"

                comments = [comment.model_dump_json() for comment in issue.comments]
                response += f"<issue_{issue.ticket_number}_comments>{comments}</issue_{issue.ticket_number}_comments>"

            response += "</issues>"
            return [], response

        except Exception as e:
            logger.error(f"Failed to query issues: {str(e)}")
            logger.error(traceback.format_exc())
            return []
