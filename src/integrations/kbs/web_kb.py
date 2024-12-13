from typing import Any, Coroutine, List, Tuple
from uuid import UUID
import requests
import json
import os

from src.integrations.kbs.base_kb import KnowledgeBaseResponse
from .base_kb import BaseKnowledgeBase

EXA_SEARCH_URL = "https://api.exa.ai/search"


class WebKnowledgeBase(BaseKnowledgeBase):
    """
    WebKB is a knowledge base for the web. It is a collection of all the knowledge
    that we have collected from the web. Uses Exa API.
    """

    def __init__(self, org_id: UUID):
        super().__init__(org_id)
        self.exa_key = os.getenv("EXA_KEY")
        self.headers = {"x-api-key": self.exa_key, "Content-Type": "application/json"}

    def exa_request_wrapper(self, query: str):
        """
        Wrapper for the Exa API request.

        Args:
            query (str): The query to search for.
        """

        payload = {
            "query": query,
            "useAutoprompt": True,
            "type": "<string>",
            "category": "company",
            "numResults": 10,
            # "includeDomains": ["example.com", "sample.net"],
            # "excludeDomains": ["excludedomain.com", "excludeme.net"],
            # "startCrawlDate": "2023-01-01T00:00:00.000Z",
            # "endCrawlDate": "2023-12-31T00:00:00.000Z",
            # "startPublishedDate": "2023-01-01T00:00:00.000Z",
            # "endPublishedDate": "2023-12-31T00:00:00.000Z",
            # "includeText": ["electron", "positron"],
            # "excludeText": ["neutron", "elon"],
            "contents": {
                "text": {
                    # "maxCharacters": 123,
                    "includeHtmlTags": True
                },
                "highlights": {
                    # "numSentences": 123,
                    # "highlightsPerUrl": 123,
                    "query": "<string>"
                },
                # "summary": {"query": "<string>"}
            },
        }

        response = requests.post(EXA_SEARCH_URL, headers=self.headers, json=payload)
        return response.json()

    def query(
        self, query: str, limit: int = 5, tb: str | None = None, **kwargs
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
        Query the knowledge base.

        Args:
            query (str): The query to search for.
            limit (int, optional): The number of results to return. Defaults to 5.
            tb (str | None, optional): The table to search in. Defaults to None.

        Returns:
            Tuple[List[KnowledgeBaseResponse], str]: The results and the table used.
        """

        results = self.exa_request_wrapper(query)
        return [], json.dumps(results["results"][:limit])

    def index(self, data: Any) -> Coroutine[Any, Any, bool]:
        """
        Index data into the knowledge base. Not needed for this KB because we're using exa's knowledge base.
        """
        return super().index(data)
