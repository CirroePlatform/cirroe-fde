from typing import Dict, List, Any, Tuple
import json
import time
import logging
from .handle_base_action import BaseActionHandler
from include.constants import (
    EXAMPLE_CREATOR_CREATION_TOOLS,
    EXAMPLE_CREATOR_MODIFICATION_TOOLS,
    EXAMPLE_CREATOR_CLASSIFIER_TOOLS,
)
import random
import anthropic
from include.utils import format_prompt
from src.model.news import News
from src.integrations.kbs.github_kb import GithubKnowledgeBase
from src.example_creator.sandbox import Sandbox

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
        org_name: str,
        org_id: str,
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
        self.org_name = org_name
        self.org_id = org_id
        self.github_kb = GithubKnowledgeBase(org_id=self.org_id, org_name=self.org_name)
        self.product_readme = self.github_kb.get_readme(
            f"{self.org_name}/{self.product_name}"
        )
        self.sandbox = Sandbox()
        self.preamble = None

    def __load_prompts(self):
        with open(self.action_classifier_prompt, "r") as f:
            self.action_classifier_prompt = f.read()
        with open(self.execute_creation_prompt, "r") as f:
            self.execute_creation_prompt = f.read()
        with open(self.execute_modification_prompt, "r") as f:
            self.execute_modification_prompt = f.read()

    def craft_pr_title_and_body(
        self, messages: List[any]
    ) -> Tuple[str, str, str, str]:
        """
        Craft a PR title and body from the messages

        Args:
            messages (List[any]): List of messages from the tools calling chain

        Returns:
            Tuple[str, str, str, str]: PR title, description, commit message, and branch name
        """
        with open("include/prompts/example_builder/pr_title_and_desc.txt", "r") as f:
            pr_title_and_desc_prompt = f.read()
            # Filter messages to only include code_files and action tags
            filtered_messages = [
                msg for msg in messages 
                if any(tag in msg.get("content", "") 
                      for tag in ["<code_files>", "</code_files>", "<action>", "</action>"])
            ]
            
            pr_title_and_desc_prompt = format_prompt(
                pr_title_and_desc_prompt,
                preamble=self.preamble,
                messages=json.dumps(filtered_messages),
                product_name=self.product_name,
            )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": pr_title_and_desc_prompt}],
        )

        title = (
            response.content[0].text.split("<title>")[1].split("</title>")[0].strip()
        )
        description = (
            response.content[0]
            .text.split("<description>")[1]
            .split("</description>")[0]
            .strip()
        )
        commit_msg = (
            response.content[0]
            .text.split("<commit_msg>")[1]
            .split("</commit_msg>")[0]
            .strip()
        )
        branch_name = (
            response.content[0]
            .text.split("<branch_name>")[1]
            .split("</branch_name>")[0]
            .strip()
        )

        return title, description, commit_msg, branch_name

    def _handle_action_case(self, action_type, prompt, tools, step_messages):
        """Helper function to handle create/modify action cases"""
        self.tools = tools
        cur_prompt = prompt
        if step_messages[-1]["role"] != "user":
            action_msg = "create a new" if action_type == "create" else "modify an existing"
            step_messages += [
                {
                    "role": "user", 
                    "content": f"We've identified a need to {action_msg} example, now let's continue to develop the example based on all previous information."
                }
            ]
        return cur_prompt

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
            self.preamble = preamble
            self.action_classifier_prompt = format_prompt(
                self.action_classifier_prompt,
                preamble=preamble,
                product_name=self.product_name,
                product_readme=self.product_readme,
            )
            self.execute_creation_prompt = format_prompt(
                self.execute_creation_prompt,
                product_name=self.product_name,
                preamble=preamble,
            )
            self.execute_modification_prompt = format_prompt(
                self.execute_modification_prompt,
                product_name=self.product_name,
                preamble=preamble,
            )

        news_values = list(news_stream.values())
        random.shuffle(news_values)
        news_string = "\n".join(
            [news.model_dump_json() for news in news_values]
        )
        step_size = len(news_string) // 2
        cur_prompt = self.action_classifier_prompt
        self.tools = EXAMPLE_CREATOR_CLASSIFIER_TOOLS

        for i in range(0, len(news_string), step_size):
            step_messages = [
                {
                    "role": "user",
                    "content": f"<news>{news_string[i : i + step_size]}</news>",
                }
            ]

            step_response = super().handle_action(
                step_messages, max_tool_calls, system_prompt=cur_prompt
            )
            last_message = step_response["response"]

            # 1. if the response has the <action></action> tag in the last message, then we can reset the correct prompt and tools
            action: str | None = None
            if (
                cur_prompt == self.action_classifier_prompt
                and "<action>" in last_message
            ):
                action = (
                    last_message.split("<action>")[1].split("</action>")[0].strip()
                )

            if action == "create":
                cur_prompt = self._handle_action_case(
                    "create",
                    self.execute_creation_prompt,
                    EXAMPLE_CREATOR_CREATION_TOOLS,
                    step_messages
                )
            elif action == "modify":
                cur_prompt = self._handle_action_case(
                    "modify", 
                    self.execute_modification_prompt,
                    EXAMPLE_CREATOR_MODIFICATION_TOOLS,
                    step_messages
                )
            elif action == "none":
                time.sleep(60) # Just so we don't overload the anthropic API
                continue

            step_response = super().handle_action(step_messages, max_tool_calls, system_prompt=cur_prompt)
            last_message = step_response["response"]
            if ("<files>" in last_message):
                title, description, commit_msg, branch_name = self.craft_pr_title_and_body(
                    step_messages
                )
                self.sandbox.create_github_pr(
                    last_message,
                    # f"{self.org_name}/{self.product_name}", TODO: change this back after we finish mocking the demo
                    "Cirr0e/firecrawl-examples",
                    title,
                    description,
                    commit_msg,
                    branch_name,
                )

                logging.info("PR created successfully")

            time.sleep(60) # Just so we don't overload the anthropic API

        return {"content": "Completed news stream processing"}
