import logging
from bs4 import BeautifulSoup
from src.integrations.cleaners.base_cleaner import BaseCleaner

class HTMLCleaner(BaseCleaner):
    """
    Cleans HTML content by removing unwanted elements and normalizing whitespace.
    """

    # Elements to remove completely
    SCRIPT_ELEMENTS = ["script", "style", "svg", "path"]
    
    # Classes to remove
    NON_CONTENT_CLASSES = [
        "sr-only",
        "js-clipboard-copy-icon", 
        "octicon",
        "zeroclipboard-container"
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def clean(self, html_content: str) -> str:
        """
        Clean HTML content by removing unwanted elements and normalizing whitespace.

        Args:
            html_content (str): Raw HTML content to clean

        Returns:
            str: Cleaned HTML content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script elements
            for element in self.SCRIPT_ELEMENTS:
                for tag in soup.find_all(element):
                    tag.decompose()

            # Remove elements with non-content classes
            for class_name in self.NON_CONTENT_CLASSES:
                for tag in soup.find_all(class_=class_name):
                    tag.decompose()

            # Get text and normalize whitespace
            text = soup.get_text(separator=' ', strip=True)
            
            # Remove extra whitespace
            text = ' '.join(text.split())

            return text

        except Exception as e:
            self.logger.error(f"Error cleaning HTML content: {str(e)}")
            return html_content
