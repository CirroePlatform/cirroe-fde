from dotenv import load_dotenv
from itertools import chain
from typing import List, Tuple

import tiktoken
import requests
import logger
import uuid
import re
import httpx
import base64

load_dotenv()

def get_latest_version(package_name: str) -> Tuple[List[str], str]:
    """
    Fetches the latest version of a given pip dependency from PyPI.
    
    Args:
        package_name (str): The name of the pip dependency.
    
    Returns:
        str: The latest version of the package, or an error message if the package is not found.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        data = response.json()
        return [], data['info']['version']
    except requests.exceptions.HTTPError as http_err:
        return [], f"HTTP error occurred: {http_err}"
    except requests.exceptions.RequestException as req_err:
        return [], f"Request error occurred: {req_err}"
    except KeyError:
        return [], "Unexpected response format from PyPI."
    except Exception as err:
        return [], f"An error occurred: {err}"


def format_prompt(prompt: str, **kwargs) -> str:
    """
    Formats a prompt string with given variables.

    Args:
        prompt (str): The input prompt containing placeholders.
        **kwargs: Variables to replace in the prompt.

    Returns:
        str: A partially formatted prompt.
    """
    # Regular expression to match placeholders in the prompt
    placeholders = re.findall(r"\{(.*?)\}", prompt)

    # Replace only the placeholders that are provided in kwargs
    for placeholder in placeholders:
        if placeholder in kwargs:
            prompt = prompt.replace(f"{{{placeholder}}}", str(kwargs[placeholder]))

    return prompt


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
    elif response.status_code != 200:
        logger.error(
            "Failed to get image from link: %s, response code: %s",
            link,
            response.status_code,
        )
        return None

    media_type = response.headers["Content-Type"]
    img_data = base64.standard_b64encode(response.content).decode("utf-8")
    return (img_data, media_type)
