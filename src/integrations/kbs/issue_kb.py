import re
import json
import traceback
from typing import Dict, List, Tuple
from uuid import UUID
from anthropic import Anthropic
from src.model.issue import Issue
from src.integrations.kbs.base_kb import BaseKnowledgeBase, KnowledgeBaseResponse

from src.storage.vector import VectorDB

from logger import logger

from include.constants import MODEL_HEAVY, COALESCE_ISSUE_PROMPT


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

    def __get_git_image_links_from_kbres(
        self, kbres: KnowledgeBaseResponse
    ) -> List[str]:
        """
        Extract image links from a KnowledgeBaseResponse object
        Args:
            kbres (KnowledgeBaseResponse): KnowledgeBaseResponse object

        Returns:
            List[str]: List of image links
        """
        pattern = r'!\[[^\]]*\]\((.*?)\s*("(?:.*[^"])")?\s*\)'
        matches = re.findall(pattern, kbres.content)

        return [match[0] for match in matches]

    def query(
        self, query: str, limit: int = 5
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

            results = []
            # for _, issue_data in issues.items(): # TODO uncomment this when we'r handling knowledge base responses in debug_issue
            #     metadata = json.loads(issue_data["metadata"])

            #     results.append(
            #         KnowledgeBaseResponse(
            #             content=issue_data["metadata"],
            #             metadata=metadata,
            #             source=f"Issue #{metadata['ticket_number']}" if metadata["ticket_number"] else "",
            #             relevance_score=issue_data["similarity"],
            #         )
            #     )

            return results, f"<issues>{json.dumps(issues)}</issues>"

        except Exception as e:
            logger.error(f"Failed to query issues: {str(e)}")
            logger.error(traceback.format_exc())
            return []
