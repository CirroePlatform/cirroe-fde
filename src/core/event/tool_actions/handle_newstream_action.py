from typing import Dict, List, Any
import logging
from .handle_base_action import BaseActionHandler
from include.constants import EXAMPLE_CREATOR_CREATION_TOOLS, EXAMPLE_CREATOR_MODIFICATION_TOOLS
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
        execute_modification_prompt: str,
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
            model=model,
        )
        self.execute_creation_prompt = execute_creation_prompt
        self.execute_modification_prompt = execute_modification_prompt

    def handle_action(
        self, news_stream: List[News], max_tool_calls: int = 15
    ) -> Dict[str, Any]:
        """
        Handle processing a news stream to determine and execute appropriate action

        Args:
            news_stream: Initial message stream containing news source
            max_tool_calls: Maximum number of tool calls allowed

        Returns:
            Dict containing final response and collected knowledge base responses
        """
        
        with open("prompts/example_builder/preamble.txt", "r") as f:
            preamble = f.read()

        step_messages = []
        for _ in range(max_tool_calls):
            news_string = "\n".join([news.model_dump_json() for news in news_stream])
            step_messages += [{"role": "user", "content": news_string}]

            step_response = super().handle_action(step_messages, 1, step_by_step=True)
            last_message = step_response["last_response"].content[0].text
            step_messages.append(last_message)

            # 1. if the response has the <action></action> tag in the last message, then we can reset the correct prompt and tools
            if self.system_prompt_file == self.action_classifier_prompt:
                for content in step_response.get("content", []):
                    if isinstance(content, str) and "<action>" in content:
                        action = content.split("<action>")[1].split("</action>")[0].strip()

                        if action == "create":
                            self.tools = EXAMPLE_CREATOR_CREATION_TOOLS
                            creation_prompt = self.execute_creation_prompt.format(
                                product_name="firecrawl",
                                new_technology="new_tech",
                                preamble=preamble,
                            )
                            self.system_prompt_file = creation_prompt
                        elif action == "modify":
                            self.system_prompt_file = self.execute_modification_prompt
                            self.tools = EXAMPLE_CREATOR_MODIFICATION_TOOLS
                        elif action == "none":
                            return {"content": "No action needed for this news stream"}

            # 2. If the last tool called was the pr opener, then we can end with the last message.
