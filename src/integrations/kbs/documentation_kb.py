from uuid import UUID
import traceback
import logging
import os
from bs4 import BeautifulSoup
from lxml import etree
from typing import List
from src.integrations.kbs.base_kb import BaseKnowledgeBase, KnowledgeBaseResponse
import requests


class DocumentationKnowledgeBase(BaseKnowledgeBase):
    def __init__(self, org_id: UUID):
        logging.info(f"Initializing DocumentationKnowledgeBase for org_id: {org_id}")
        super().__init__(org_id)

    def _parse_sitemap(self, url: str) -> List[str]:
        """
        Get the XML representation of the documentation page.
        """
        logging.info(f"Starting to parse sitemap for URL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Customize the selector according to the website structure
            links = []
            logging.info("Extracting links from sitemap")
            for a_tag in soup.select("a[href]"):  # TODO Adjust selector as needed
                href = a_tag.get("href")
                # Ensure link is absolute or properly formatted
                full_url = href if href.startswith("http") else url + href
                logging.debug(f"Found link: {full_url}")
                links.append(full_url)

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
            logging.info(f"Successfully fetched content from {url}")
            return response.text
        except requests.RequestException as e:
            logging.error(f"Failed to fetch page content: {str(e)}")
            raise

    def _get_sitemap_path(self) -> str:
        return f"scripts/data/sitemaps/{self.org_id}.xml"

    def _index_tree(self, tree: etree.ElementTree):
        """
        Index the XML tree into the knowledge base.
        """
        pass

    async def index(self, url: str) -> bool:
        """
        Index a documentation repository into the knowledge base.

        Args:
            url (str): The base documentation page to index, as a url.

        Returns:
            bool: True if the documentation page was indexed successfully, False otherwise.
        """
        logging.info(f"Starting documentation indexing for {url}")

        if os.path.exists(self._get_sitemap_path()):
            tree = etree.parse(self._get_sitemap_path())
            self._index_tree(tree)
            return True

        try:
            links = self._parse_sitemap(url)
            root = etree.Element(f"Documentation_{self.org_id}")
            logging.info(f"Processing {len(links)} pages for indexing")

            for link in links:
                logging.debug(f"Processing link: {link}")
                node = etree.SubElement(root, "Page", url=link)

                # 1. fetch page content
                content = self._fetch_page_content(link)
                # 2. create xml tree
                content_node = etree.SubElement(node, "Content")
                content_node.text = content
                logging.debug(f"Successfully processed content for {link}")

            # 3. save tree to file
            logging.info("Saving XML tree to file")
            tree = etree.ElementTree(root)

            smpath = self._get_sitemap_path()
            if not os.path.exists(smpath):
                logging.info(f"Creating directory for sitemap at {smpath}")
                os.makedirs(os.path.dirname(smpath), exist_ok=True)

            tree.write(smpath, encoding="utf-8", xml_declaration=True)
            logging.info(f"Successfully saved XML tree to {smpath}")

            # 4. index tree
            logging.info("Starting tree indexing")
            self._index_tree(tree)

            logging.info("Successfully completed documentation indexing")
            return True

        except Exception as e:
            logging.error(f"Failed to index documentation: {str(e)}")
            logging.error(traceback.format_exc())
            return False

    async def query(self, query: str, limit: int = 5) -> List[KnowledgeBaseResponse]:
        """
        Retrieve a list of documentation pages that match the query.

        Args:
            query (str): The search query in natural language format.
            limit (int): The number of documents to retrieve

        Returns:
            List[KnowledgeBaseResponse]: List of documentation responses that match the search query
        """
        logging.warning("Query functionality not implemented yet")
