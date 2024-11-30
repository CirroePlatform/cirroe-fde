from dataclasses import dataclass
from typing import Optional, List, Dict, Any
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

class HandleDiscordMessage(BaseActionHandler):
    def __init__(self, org_id: str):
        self.org_id = org_id

        # Set up the same tools as HandleIssue
        userdata = SupaClient(user_id=self.org_id).get_user_data(ORG_NAME, REPO_NAME, debug=True)
        repo = Repository(remote="github.com", repository=userdata[REPO_NAME], branch="main")
        search_tools = SearchTools(self.org_id, [repo])
        self.tools_map = {
            "execute_codebase_search": search_tools.execute_codebase_search,
            "execute_documentation_search": search_tools.execute_documentation_search,
            "execute_issue_search": search_tools.execute_issue_search,
        }

        super().__init__(
            anthropic.Anthropic(api_key=ANTHROPIC_API_KEY),
            DEBUG_DISCORD_FILE,
            DEBUG_TOOLS,
            self.tools_map,
            MODEL_HEAVY
        )

    def construct_initial_messages(self, message: DiscordMessage) -> List[Dict[str, Any]]:
        """
        Construct the initial message stream for the Discord message.

        Args:
            message: The Discord message to construct the message stream for

        Returns:
            List[Dict[str, Any]]: The initial message stream
        """
        return [
            {
                "role": "user",
                "content": (
                    f"Discord message from {message.author} "
                    f"in channel {message.channel_id}:\n\n{message.content}"
                )
            }
        ]

    def handle_discord_message(
        self,
        message: DiscordMessage,
        max_tool_calls: int = 3
    ) -> Dict[str, Any]:
        """
        Process a Discord message and generate a response using the AI agent.

        Args:
            message: The Discord message to process
            max_tool_calls: Maximum number of tool calls allowed (default: 3)

        Returns:
            Dict containing the final response and collected KB responses
        """
        # Construct initial message stream
        messages = self.construct_initial_messages(message)
        
        # Use the base class's handle_action method to process the message
        response = self.handle_action(messages, max_tool_calls)

        return response
