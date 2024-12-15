from typing import List, Dict, Any, Tuple
from include.utils import get_base64_from_url
import logging
import anthropic
from dotenv import load_dotenv
import os

from src.core.event.user_actions.handle_base_action import BaseActionHandler
from src.storage.supa import SupaClient
from src.core.tools import SearchTools
from src.model.issue import DiscordMessage
from src.integrations.kbs.github_kb import Repository
from include.constants import (
    DEBUG_DISCORD_FILE,
    DEBUG_TOOLS,
    MODEL_HEAVY,
    ORG_NAME,
    REPO_NAME,
)

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


class DiscordMessageHandler(BaseActionHandler):
    def __init__(self, org_id: str):
        self.org_id = org_id

        # Set up the same tools as HandleIssue
        userdata = SupaClient(user_id=self.org_id).get_user_data(
            ORG_NAME, REPO_NAME, debug=True
        )
        repo = Repository(
            remote="github.com", repository=userdata[REPO_NAME], branch="main"
        )
        search_tools = SearchTools(self.org_id, [repo])
        self.tools_map = {
            "execute_search": search_tools.execute_search,
        }

        super().__init__(
            anthropic.Anthropic(api_key=ANTHROPIC_API_KEY),
            DEBUG_DISCORD_FILE,
            DEBUG_TOOLS,
            self.tools_map,
            MODEL_HEAVY,
        )

    def __get_img_links_from_message(
        self, message: DiscordMessage
    ) -> List[Tuple[str, str]]:
        """
        Get the image links from a Discord message

        Args:
            message (DiscordMessage): The Discord message to get the image links from

        Returns:
            List[Tuple[str, str]]: The image links and media types from the message
        """
        return [(attachment[0], attachment[1]) for attachment in message.attachments]

    def construct_initial_messages(
        self, message: DiscordMessage
    ) -> List[Dict[str, Any]]:
        """
        Construct the initial message stream for the Discord message.

        Args:
            message: The Discord message to construct the message stream for

        Returns:
            List[Dict[str, Any]]: The initial message stream
        """
        image_links_and_types = self.__get_img_links_from_message(message)

        image_base64s = []
        for link, media_type in image_links_and_types:
            img_data, _ = get_base64_from_url(link)
            if img_data:
                image_base64s.append((img_data, media_type))

        # Initialize message stream with issue description and any comments
        messages = [
            {"role": "user", "content": message.content},
        ]

        if image_base64s:
            messages[0]["content"] = [
                {"type": "text", "text": messages[0]["content"]},
                *[
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": data,
                        },
                    }
                    for data, media_type in image_base64s
                ],
            ]

        return messages

    def handle_discord_message(
        self, message: DiscordMessage, max_tool_calls: int = 5
    ) -> Dict[str, Any]:
        """
        Process a Discord message and generate a response using the AI agent.

        Args:
            message: The Discord message to process
            max_tool_calls: Maximum number of tool calls allowed (default: 5)

        Returns:
            Dict containing the final response and collected KB responses
        """
        # Construct initial message stream
        messages = self.construct_initial_messages(message)

        # Use the base class's handle_action method to process the message
        response = self.handle_action(messages, max_tool_calls=max_tool_calls)

        if response["response"]:
            return response

        logging.info(f"Discord responses didn't work, raw response: {response}")

        return response
