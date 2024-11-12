from src.integrations.kbs.base_kb import BaseKnowledgeBase, KnowledgeBaseResponse
from src.integrations.cleaners.html_cleaner import HTMLCleaner
from src.model.documentation import DocumentationPage
from include.constants import MODEL_HEAVY
from src.storage.vector import VectorDB
from anthropic import Anthropic
from typing import List, Tuple
from lxml import etree
from uuid import UUID
import traceback
import requests
import hashlib
import logging
import json


class DocumentationKnowledgeBase(BaseKnowledgeBase):
    def __init__(self, org_id: UUID):
        logging.info(f"Initializing DocumentationKnowledgeBase for org_id: {org_id}")
        self.vector_db = VectorDB(org_id)
        self.html_cleaner = HTMLCleaner()
        self.client = Anthropic()
        super().__init__(org_id)

    def _parse_links_from_sitemap(self, url: str) -> List[str]:
        """
        Get the list of links from the sitemap.
        """
        logging.info(f"Starting to parse sitemap for URL: {url}")

        try:
            response = requests.get(url)
            response.raise_for_status()
            links = []

            logging.info("Extracting links from sitemap")

            # Parse sitemap XML using lxml for better XML handling
            tree = etree.fromstring(response.content)

            # Find all loc elements which contain URLs in sitemap XML format
            for loc in tree.xpath(
                "//xmlns:loc",
                namespaces={"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"},
            ):
                url = loc.text
                logging.debug(f"Found link: {url}")
                links.append(url)

            # Also check for sitemap index files that contain other sitemaps
            for sitemap in tree.xpath(
                "//xmlns:sitemap/xmlns:loc",
                namespaces={"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"},
            ):
                sitemap_url = sitemap.text
                logging.debug(f"Found sitemap: {sitemap_url}")
                # Recursively parse nested sitemaps
                links.extend(self._parse_links_from_sitemap(sitemap_url))

            logging.info(f"Successfully parsed sitemap, found {len(links)} links")
            return links
        except requests.RequestException as e:
            logging.error(f"Failed to parse sitemap: {str(e)}")
            raise

    def _fetch_page_content(self, url: str) -> str:
        """
        Fetch the content of a page.
        """
        logging.info(f"Fetching content from URL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            retval = self.html_cleaner.clean(response.text)
            logging.info(f"Successfully fetched content from {url}")

            return retval
        except requests.RequestException as e:
            logging.error(f"Failed to fetch page content: {str(e)}")
            raise

    def _get_page_primary_key(self, url: str) -> str:
        url_hash = hashlib.sha3_256(url.encode()).digest()
        return url_hash.hex()

    def _index_links(self, links: List[str]):
        """
        Index the list of links into the knowledge base by adding each page to the vector database.
        """
        logging.info("Indexing list of links into vector database")

        for url in links:
            content = self._fetch_page_content(url)

            try:
                logging.debug(f"Adding page {url} to vector database")
                page = DocumentationPage(
                    primary_key=self._get_page_primary_key(url),
                    url=url,
                    content=content,
                )
                self.vector_db.add_documentation_page(page)
                logging.debug(f"Successfully added {url} to vector database")
            except Exception as e:
                logging.error(
                    f"Failed to add {url} to vector database: {str(e)}. Skipping..."
                )
                continue

        logging.info("Finished indexing list of links")

    async def index(self, url: str) -> bool:
        """
        Index a documentation repository into the knowledge base.

        Args:
            url (str): The base documentation page's sitemap url to index.

        Returns:
            bool: True if the sitemap was indexed successfully, False otherwise.
        """
        logging.info(f"Starting documentation indexing for {url}")

        try:
            links = self._parse_links_from_sitemap(url)
            self._index_links(links)

            return True

        except Exception as e:
            logging.error(f"Failed to index documentation: {str(e)}")
            logging.error(traceback.format_exc())

            return False

    def query(
        self, query: str, limit: int = 5
    ) -> Tuple[List[KnowledgeBaseResponse], str]:
        """
        Retrieve a list of documentation pages that match the query.

        Args:
            query (str): The search query in natural language format.
            limit (int): The number of documents to retrieve

        Returns:
            Tuple[List[KnowledgeBaseResponse], str]: List of documentation responses that match the search query,
                      String answer to the query
        """
        try:
            query_vector = self.vector_db.vanilla_embed(query)
            results = self.vector_db.get_top_k_documentation(
                limit, query_vector
            )  # TODO seeing similarity scores of 1. that seems off

            kb_responses = []
            for result in results.values():
                metadata = json.loads(result["metadata"])
                kb_response = KnowledgeBaseResponse(
                    source="documentation",
                    content=metadata["content"],
                    relevance_score=result["similarity"],
                    metadata=metadata,
                )
                kb_responses.append(kb_response)

            messages = [
                {"role": "user", "content": query},
                {
                    "role": "assistant",
                    "content": "Here are the documentation pages I found that match your query:",
                },
                {"role": "user", "content": json.dumps(results)},
            ]

            response = self.client.messages.create(
                model=MODEL_HEAVY,
                max_tokens=1024,
                messages=messages,
            )

            return kb_responses, response.content[0].text
        except Exception as e:
            logging.error(f"Failed to query documentation: {str(e)}")
            logging.error(traceback.format_exc())
            return [], str(e)
