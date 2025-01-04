from typing import Dict, List, Any
import logging
from .handle_base_action import BaseActionHandler
from include.constants import (
    EXAMPLE_CREATOR_CREATION_TOOLS,
    EXAMPLE_CREATOR_MODIFICATION_TOOLS,
    EXAMPLE_CREATOR_CLASSIFIER_TOOLS,
)
import anthropic
from include.utils import format_prompt
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
        product_name: str,
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
        self.action_classifier_prompt = action_classifier_prompt
        self.execute_creation_prompt = execute_creation_prompt
        self.execute_modification_prompt = execute_modification_prompt
        self.product_name = product_name

    def __load_prompts(self):
        with open(self.action_classifier_prompt, "r") as f:
            self.action_classifier_prompt = f.read()
        with open(self.execute_creation_prompt, "r") as f:
            self.execute_creation_prompt = f.read()
        with open(self.execute_modification_prompt, "r") as f:
            self.execute_modification_prompt = f.read()

    def handle_action(
        self, news_stream: Dict[str, News], max_tool_calls: int = 15
    ) -> Dict[str, Any]:
        """
        Handle processing a news stream to determine and execute appropriate action

        Args:
            news_stream: Initial message stream containing news source
            max_tool_calls: Maximum number of tool calls allowed

        Returns:
            Dict containing final response and collected knowledge base responses
        """
        self.__load_prompts()

        with open("include/prompts/example_builder/preamble.txt", "r") as f:
            preamble = f.read()
            self.action_classifier_prompt = format_prompt(
                self.action_classifier_prompt,
                preamble=preamble,
                product_name=self.product_name,
            )
            self.execute_creation_prompt = format_prompt(
                self.execute_creation_prompt,
                product_name=self.product_name,
                new_technology="new_tech",
                preamble=preamble,
            )
            self.execute_modification_prompt = format_prompt(
                self.execute_modification_prompt,
                product_name=self.product_name,
                preamble=preamble,
            )

        news_string = "\n".join(
            [news.model_dump_json() for news in news_stream.values()]
        )
        step_size = len(news_string) // 3
        cur_prompt = self.action_classifier_prompt
        self.tools = EXAMPLE_CREATOR_CLASSIFIER_TOOLS

        for i in range(0, len(news_string), step_size):
            step_messages = [
                {"role": "user", "content": news_string[i : i + step_size]}
            ]

            for _ in range(max_tool_calls):
                step_response = super().handle_action(
                    step_messages, 1, step_by_step=True, system_prompt=cur_prompt
                )
                last_message = step_response["last_response"].content[0].text

                # 1. if the response has the <action></action> tag in the last message, then we can reset the correct prompt and tools
                if cur_prompt == self.action_classifier_prompt:
                    for content in step_response.get("content", []):
                        if (
                            isinstance(content, str) and "<action>" in content
                        ) or "<action>" in last_message:
                            action = (
                                content.split("<action>")[1]
                                .split("</action>")[0]
                                .strip()
                            )

                            if action == "create":
                                cur_prompt = self.execute_creation_prompt
                                self.tools = EXAMPLE_CREATOR_CREATION_TOOLS
                            elif action == "modify":
                                cur_prompt = self.execute_modification_prompt
                                self.tools = EXAMPLE_CREATOR_MODIFICATION_TOOLS
                            elif action == "none":
                                return {
                                    "content": "No action needed for this news stream"
                                }

                # 2. If the last message has the <updated_example> tag, then we can end with the last message, open a PR, and return out of this function.
