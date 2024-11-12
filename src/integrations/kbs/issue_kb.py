import json
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

    def __respond_to_query(self, issues: List[KnowledgeBaseResponse], query: str) -> str:
        """
        Generate a natural language response to a query given a list of KnowledgeBaseResponse objects
        """
        pass

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

    def query(self, query: str, limit: int = 5) -> Tuple[List[KnowledgeBaseResponse], str]:
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
            for issue_id, issue_data in issues.items():

                results.append(
                    KnowledgeBaseResponse(
                        content=issue_data["metadata"],
                        metadata=json.loads(issue_data["metadata"]),
                        source=f"Ticket #{issue_id}",
                        relevance_score=issue_data["similarity"],
                    )
                )
                
            with open(COALESCE_ISSUE_PROMPT, "r", encoding="utf8") as fp:
                sysprompt = fp.read()
             
            messages = [
                {"role": "user", "content": f"input query: {query}\nsimilar_issues: {json.dumps(issues)}"}
            ]

            response = self.client.messages.create(
                model=MODEL_HEAVY,
                system=sysprompt,
                max_tokens=2048,
                messages=messages,
            )

            return results, response.content[0].text

        except Exception as e:
            logger.error(f"Failed to query issues: {str(e)}")
            return []
