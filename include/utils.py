from dotenv import load_dotenv
from itertools import chain
from typing import List, Tuple

import tiktoken
import logger
import uuid
import re
import httpx
import base64

load_dotenv()


def num_tokens_from_string(string: str, model_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_git_image_links(content: str) -> List[str]:
    """
    Extract image links from a string of content
    Args:
        content: Content to chunk into image links

    Returns:
        List[str]: List of image links
    """
    pattern = r'!\[[^\]]*\]\((.*?)\s*("(?:.*[^"])")?\s*\)'
    matches = re.findall(pattern, content)

    valid_links = [match for match in list(chain(*matches)) if match.startswith("http")]
    if valid_links:
        return valid_links

    # Basic pattern for GitHub user attachment links
    pattern = r"https://github\.com/user-attachments/assets/[a-fA-F0-9-]+"

    # Find all potential matches
    potential_links = re.findall(pattern, content)

    # Validate each link to ensure the UUID part is valid
    for link in potential_links:
        # Extract the UUID part (everything after the last /)
        potential_uuid = link.split("/")[-1]

        try:
            # Try to parse it as a UUID to validate
            uuid.UUID(potential_uuid)
            valid_links.append(link)
        except ValueError:
            continue

    return valid_links


def get_base64_from_url(link: str) -> Tuple[str, str]:
    """
    Get the base64 encoded image from a URL.

    Args:
        link (str): URL to get the image from

    Returns:
        Tuple[str, str]: Base64 encoded image and media type
    """
    response = httpx.get(link)
    if response.status_code == 302:
        response = httpx.get(response.headers["Location"])
    else:
        logger.error("Failed to get image from link: %s", link)
        return None

    media_type = response.headers["Content-Type"]
    img_data = base64.standard_b64encode(response.content).decode("utf-8")
    return (img_data, media_type)
