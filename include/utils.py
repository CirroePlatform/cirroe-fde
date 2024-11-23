from dotenv import load_dotenv
from typing import List
import tiktoken
import uuid
import re

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

    retval = [match for match in matches]

    if retval and retval[0].startswith("http"):
        return retval

    # Basic pattern for GitHub user attachment links
    pattern = r'https://github\.com/user-attachments/assets/[a-fA-F0-9-]+'
    
    # Find all potential matches
    potential_links = re.findall(pattern, content)
    
    # Validate each link to ensure the UUID part is valid
    valid_links = []
    for link in potential_links:
        # Extract the UUID part (everything after the last /)
        potential_uuid = link.split('/')[-1]
        
        try:
            # Try to parse it as a UUID to validate
            uuid.UUID(potential_uuid)
            valid_links.append(link)
        except ValueError:
            continue

    return valid_links