from typing import Dict, List, Any
import logging
from .handle_base_action import BaseActionHandler
from include.constants import EXAMPLE_CREATOR_TOOLS
import anthropic
from src.model.news import News

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
        self, messages: List[News], max_tool_calls: int = 5, is_creation: bool = False
    ) -> Dict[str, Any]:
        """
        Handle processing a news stream to determine and execute appropriate action

        Args:
            messages: Initial message stream containing news source
            max_tool_calls: Maximum number of tool calls allowed

        Returns:
            Dict containing final response and collected knowledge base responses
        """

        # First classify the action using action classifier prompt. Convert the news to a string.
        action = None
        if not is_creation:
            news_string = "\n".join([news.model_dump_json() for news in messages])
            messages = [{"role": "user", "content": news_string}]
        
            action_response = super().handle_action(messages, max_tool_calls)
            # Extract action from response
            for content in action_response.get("content", []):
                if isinstance(content, str) and "<action>" in content:
                    action = content.split("<action>")[1].split("</action>")[0].strip()
                    break

            if not action:
                logger.warning("No action classified from news stream")
                return {"content": "No action needed for this news stream"}
        else:
            action = "create"

        # Update system prompt based on classified action
        if action == "create": # TODO different tools needed
            self.system_prompt_file = self.execute_creation_prompt
            
            # product_name
            # new_technology
            # Format creation prompt with product name and new technology
            creation_prompt = self.execute_creation_prompt.format(
                product_name="firecrawl",
                new_technology="new_tech",
                preamble="You are an AI assistant helping to create examples."
            )
            self.system_prompt_file = creation_prompt
            
            self.tools = EXAMPLE_CREATOR_TOOLS
        elif action == "modify":
            self.system_prompt_file = self.execute_modification_prompt
            self.tools = EXAMPLE_CREATOR_TOOLS
        else:
            return {"content": "No action needed for this news stream"}

        # Execute the creation/modification action
        return super().handle_action(messages, max_tool_calls)
