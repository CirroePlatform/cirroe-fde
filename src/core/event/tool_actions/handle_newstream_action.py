from typing import Dict, List, Any
import logging
from .handle_base_action import BaseActionHandler
from include.constants import EXAMPLE_CREATOR_TOOLS
import anthropic

logger = logging.getLogger(__name__)

class NewStreamActionHandler(BaseActionHandler):
    """Handler for processing news streams and creating/modifying examples"""

    def __init__(
        self,
        client: anthropic.Anthropic,
        tools: List[Dict],
        tools_map: Dict,
        model: str,
        action_classifier_prompt: str,
        execute_creation_prompt: str, 
        execute_modification_prompt: str
    ):
        """
        Initialize the news stream action handler

        Args:
            client: Anthropic client
            tools: List of available tools and schemas
            tools_map: Mapping of tool names to implementations
            model: Model to use for completions
            action_classifier_prompt: Path to action classifier prompt
            execute_creation_prompt: Path to example creation prompt
            execute_modification_prompt: Path to example modification prompt
        """
        super().__init__(
            client=client,
            system_prompt_file=action_classifier_prompt,
            tools=tools,
            tools_map=tools_map,
            model=model
        )
        self.execute_creation_prompt = execute_creation_prompt
        self.execute_modification_prompt = execute_modification_prompt

    def handle_action(
        self, messages: List[Dict], max_tool_calls: int = 5
    ) -> Dict[str, Any]:
        """
        Handle processing a news stream to determine and execute appropriate action

        Args:
            messages: Initial message stream containing news source
            max_tool_calls: Maximum number of tool calls allowed

        Returns:
            Dict containing final response and collected knowledge base responses
        """

        # First classify the action using action classifier prompt
        action_response = super().handle_action(messages, max_tool_calls)

        # Extract action from response
        action = None
        for content in action_response.get("content", []):
            if isinstance(content, str) and "<action>" in content:
                action = content.split("<action>")[1].split("</action>")[0].strip()
                break

        if not action:
            logger.warning("No action classified from news stream")
            return {"content": "No action needed for this news stream"}

        # Update system prompt based on classified action
        if action == "create": # TODO different tools needed
            self.system_prompt_file = self.execute_creation_prompt
        elif action == "modify":
            self.system_prompt_file = self.execute_modification_prompt
        else:
            return {"content": "No action needed for this news stream"}

        # Execute the creation/modification action
        return super().handle_action(messages, max_tool_calls)
