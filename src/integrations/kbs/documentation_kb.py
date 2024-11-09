from uuid import UUID
import hashlib
import traceback
import logging
import os
from bs4 import BeautifulSoup
from lxml import etree
from typing import List
from src.integrations.kbs.base_kb import BaseKnowledgeBase, KnowledgeBaseResponse
from src.storage.vector import VectorDB
import requests
from src.model.documentation import DocumentationPage


class TreeIndexer:

    class __node:
        def __init__(self, url: str, content: str, synthetic_description: str, children: List["__node"]):
            self.url = url
            self.content = content
            self.children = children

    class __inner_node(__node):
        def __init__(self, url: str, content: str, synthetic_description: str, community_report: str, children: List["__node"], children_vector_average: float):
            super().__init__(url, content, synthetic_description, children)

            self.community_report = community_report
            self.children_vector_average = children_vector_average

    class __leaf_node(__node):
        def __init__(self, url: str, content: str, synthetic_description: str, page_content: str, vector: List[float]):
            super().__init__(url, content, synthetic_description, [])

            self.page_content = page_content
            self.vector = vector

    def __init__(self, org_id: UUID):
        self.org_id = org_id
        self.tree = None
    
    def load_tree(self, tree: etree.ElementTree):
        """
        Loads a tree into memory from the provided etree.ElementTree. Sets the self.tree attribute.

        Args:
            tree (etree.ElementTree): The tree to load into memory.
        """
        # look into how GraphRAG construction works for this
        
        # 1. Iterate through leaf nodes
        # 2. Create a vector for each leaf node
        # 3. Assign leaf nodes to specific communities 
        # 4. Set the self.tree attribute to the created tree

    def search(self, query: str, limit: int = 5) -> List[KnowledgeBaseResponse]:
        """
        Searches the tree for the most relevant nodes to the query with the DRIFT method.

        Args:
            query (str): The query to search the tree with.
            limit (int, optional): The maximum number of results to return. Defaults to 5.

        Returns:
            List[KnowledgeBaseResponse]: A list of KnowledgeBaseResponse objects containing the most relevant nodes to the query.
        """
        pass

class DocumentationKnowledgeBase(BaseKnowledgeBase):
    def __init__(self, org_id: UUID):
        logging.info(f"Initializing DocumentationKnowledgeBase for org_id: {org_id}")
        self.vector_db = VectorDB(org_id)
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
            retval = response.text
            
            logging.info(f"Successfully fetched content from {url}")
            return retval
        except requests.RequestException as e:
            logging.error(f"Failed to fetch page content: {str(e)}")
            raise

    def _get_sitemap_path(self) -> str:
        return f"scripts/data/sitemaps/{self.org_id}.xml"
    
    def _get_page_primary_key(self, url: str) -> str:
        url_hash = hashlib.sha3_256(url.encode()).digest()
        return url_hash.hex()

    def _index_tree(self, tree: etree.ElementTree):
        """
        Index the XML tree into the knowledge base by adding each page to the vector database.
        """
        root = tree.getroot()
        logging.info("Indexing XML tree into vector database")
        
        for page in root.findall("Page"):
            url = page.get("url")
            # content = page.find("Content").text # TODO uncomment, just looking for ways to clean html page
            content = self._fetch_page_content(url)

            logging.debug(f"Adding page {url} to vector database")
            
            try:
                page = DocumentationPage(primary_key=self._get_page_primary_key(url), url=url, content=content)
                self.vector_db.add_documentation_page(page)
                logging.debug(f"Successfully added {url} to vector database")
            except Exception as e:
                logging.error(f"Failed to add {url} to vector database: {str(e)}")
                continue
        
        logging.info("Finished indexing XML tree")
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
