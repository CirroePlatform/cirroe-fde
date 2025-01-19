from typing import Dict, List, Any, Tuple
import openai
import json
from cerebras.cloud.sdk import Cerebras
from src.core.event.poll import comment_on_pr
import os
import time
import logging
from .handle_base_action import BaseActionHandler
from include.constants import (
    EXAMPLE_CREATOR_CREATION_TOOLS,
    EXAMPLE_CREATOR_DEBUGGER_TOOLS,
    EXAMPLE_CREATOR_MODIFICATION_TOOLS,
    EXAMPLE_CREATOR_CLASSIFIER_TOOLS,
    EXAMPLE_CREATOR_PR_TOOLS,
    TS_KEYWORDS,
    PYTHON_KEYWORDS,
)
import random
import re
import anthropic
from include.utils import format_prompt, get_content_between_tags
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

        self.plan_generation_prompt = None
        self.thinking_model = "o1-mini"
        self.thinking_client = openai.OpenAI()

        self.cerebras_client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

    def __load_prompts(self):
        with open(self.action_classifier_prompt, "r") as f:
            self.action_classifier_prompt = f.read()
        with open(self.execute_creation_prompt, "r") as f:
            self.execute_creation_prompt = f.read()
        with open(self.execute_modification_prompt, "r") as f:
            self.execute_modification_prompt = f.read()

        with open("include/prompts/example_builder/preamble.txt", "r") as f:
            preamble = f.read()
            self.preamble = format_prompt(preamble, product_name=self.product_name)

            self.action_classifier_prompt = format_prompt(
                self.action_classifier_prompt,
                preamble=self.preamble,
                product_name=self.product_name,
                product_readme=self.product_readme,
            )
            self.execute_creation_prompt = format_prompt(
                self.execute_creation_prompt,
                product_name=self.product_name,
                preamble=self.preamble,
            )
            self.execute_modification_prompt = format_prompt(
                self.execute_modification_prompt,
                product_name=self.product_name,
                preamble=self.preamble,
            )

    def craft_pr_title_and_body(self, messages: List[any]) -> Tuple[str, str, str, str]:
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
                msg
                for msg in messages
                if any(
                    tag in msg.get("content", "")
                    for tag in [
                        "<code_files>",
                        "</code_files>",
                        "<action>",
                        "</action>",
                    ]
                )
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

        title = get_content_between_tags(response.content[0].text, "<title>", "</title>")
        description = get_content_between_tags(response.content[0].text, "<description>", "</description>")
        commit_msg = get_content_between_tags(response.content[0].text, "<commit_msg>", "</commit_msg>")
        branch_name = get_content_between_tags(response.content[0].text, "<branch_name>", "</branch_name>")

        return title, description, commit_msg, branch_name

    def _handle_action_case(self, action_type, prompt, tools, step_messages):
        """Helper function to handle create/modify action cases"""
        self.tools = tools
        cur_prompt = prompt
        if step_messages[-1]["role"] != "user":
            action_msg = (
                "create a new" if action_type == "create" else "modify an existing"
            )
            step_messages += [
                {
                    "role": "user",
                    "content": f"We've identified a need to {action_msg} example, now let's continue to develop the example based on all previous information.",
                }
            ]
        return cur_prompt

    def handle_readme_generation(
        self, code_files: str, step_messages: List[Dict[str, Any]]
    ) -> Dict[str, str] | None:
        """
        Handle the generation of a README.md file based on the code files.

        Returns the readme {path: content} dict, or None if the readme was not generated/couldn't be parsed.
        """
        readme_response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=step_messages
            + [
                {
                    "role": "user",
                    "content": f"Based on these code files, and previous messages, generate a README.md file:\n{code_files}",
                }
            ],
        )

        # Extract README content between fpath tags
        readme_content = readme_response.content[0].text

        # Find any README.md file path tag
        readme_tag_start = None
        readme_tag_end = None
        for tag in readme_content.split("<fpath_"):
            if "README.md>" in tag:
                readme_tag_start = f"<fpath_{tag.split('>')[0]}>"
                readme_tag_end = f"</fpath_{tag.split('>')[0]}>"
                break

        if readme_tag_start and readme_tag_end:
            readme_section = get_content_between_tags(
                readme_content, readme_tag_start, readme_tag_end
            )
            readme_section = {
                readme_tag_start.split("fpath_")[1].split(">")[0]: readme_section
            }
            return readme_section

        return None

    def hallucination_check(
        self, last_message: str, step_messages: List[Dict[str, Any]]
    ) -> str | None:
        """
        If the last message has some code keywords but no tags, we need to enforce the tag creation.
        """
        if PYTHON_KEYWORDS or TS_KEYWORDS in last_message:
            step_messages += [
                {
                    "role": "user",
                    "content": f"Looks like your message contains code, but I don't see the <code_files> tag or the <fpath_[actual file path]> tags anywhere, can you wrap your codefiles in those tags if you haven't already? If there are no codefiles, that's ok JUST return false and NOTHING ELSE.",
                }
            ]

            response = self.client.messages.create(
                model=self.model, max_tokens=8192, messages=step_messages
            )

            return (
                response.content[0].text.lower()
                if "false" not in response.content[0].text.lower()
                else None
            )

    def generate_design_and_implementation_plan(self, last_message: str) -> str:
        """
        Generate a design and implementation plan for the example.
        """
        with open("include/prompts/example_builder/plan_builder.txt", "r") as f:
            plan_builder_prompt = f.read()
            plan_builder_prompt = format_prompt(
                plan_builder_prompt, preamble=self.preamble, action_context=last_message
            )

            response = self.thinking_client.chat.completions.create(
                model=self.thinking_model,
                messages=[{"role": "user", "content": plan_builder_prompt}],
            )

            return response.choices[0].message.content

    def handle_code_files_pr_raise(
        self, code_files: Dict[str, str], step_messages: List[Dict[str, Any]]
    ) -> str:
        """
        Handle the creation of a PR with the code files.
        """
        # Craft the PR title and body
        title, description, commit_msg, branch_name = self.craft_pr_title_and_body(
            step_messages,
        )
        response = self.sandbox.create_github_pr(
            code_files,
            # f"{self.org_name}/{self.product_name}", TODO: change this back after we finish mocking the demo
            "Cirr0e/firecrawl-examples",
            title,
            description,
            commit_msg,
            branch_name,
        )

        return response

    def enforce_successful_sandbox_execution(
        self, code_files: Dict[str, str]
    ) -> Tuple[bool, str]:
        """
        Enforce the successful execution of the sandbox from the agent output, by appending a new user message to the step messages
        after attemtting the sandbox execution.

        Returns true if the sandbox execution was successful, false otherwise.
        """
        # 1. find the readme file from the code files
        readme_content = None
        for fpath, content in code_files.items():
            if "README.md" in fpath:
                readme_content = content
                break

        # 2. use a small call to figure out the build command and the execution command
        build_command = None
        execution_command = None
        new_message = f"Here is the README.md file for some code repo:\n{readme_content}\n\nPlease provide the build command and the execution command for the example. Return the build command in <build_command>[actual build command]</build_command> and the execution command in <execution_command>[actual execution command]</execution_command> tags. Return NOTHING ELSE."
        chat_completion = self.cerebras_client.chat.completions.create(
            messages=[{"role": "user", "content": new_message}],
            model="llama3.1-8b",
            max_tokens=4096,
        )
        response = chat_completion.choices[0].message.content
        build_command = get_content_between_tags(
            response, "<build_command>", "</build_command>"
        )
        execution_command = get_content_between_tags(
            response, "<execution_command>", "</execution_command>"
        )

        # 3. run the code with the build command
        results, str_results = self.sandbox.run_code_e2b(
            code_files, build_command, execution_command
        )

        # 4. if it failes, then we return stderr + stdout and return false.
        if not results[0].build_success or not results[0].execution_success:
            return False, str_results

        return True, str_results

    def handle_action(
        self, news_stream: Dict[str, News], max_tool_calls: int = 50
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

        news_values = list(news_stream.values())
        random.shuffle(news_values)
        news_string = "\n".join([news.model_dump_json() for news in news_values])
        step_size = len(news_string) // 3
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
                action = last_message.split("<action>")[1].split("</action>")[0].strip()

            if action == "create":
                logging.info("Creating new example...")
                cur_prompt = self._handle_action_case(
                    "create",
                    self.execute_creation_prompt,
                    EXAMPLE_CREATOR_CREATION_TOOLS,
                    step_messages,
                )
            elif action == "modify":
                logging.info("Modifying existing example...")
                cur_prompt = self._handle_action_case(
                    "modify",
                    self.execute_modification_prompt,
                    EXAMPLE_CREATOR_MODIFICATION_TOOLS,
                    step_messages,
                )
            elif action == "none":
                logging.info("No action found, continuing...")
                continue

            step_messages += [
                {
                    "role": "user",
                    "content": self.generate_design_and_implementation_plan(
                        last_message
                    ),
                }
            ]

            time.sleep(60)

            step_response = super().handle_action(
                step_messages, max_tool_calls, system_prompt=cur_prompt
            )
            last_message = step_response["response"]

            if (
                "<code_files>" not in last_message
                or "<action>none</action>" not in last_message
                or (PYTHON_KEYWORDS or TS_KEYWORDS in last_message)
            ):  # Hallucination check
                hallucination_response = self.hallucination_check(
                    last_message, step_messages
                )
                if hallucination_response:
                    last_message = hallucination_response
            else:
                code_files = self.sandbox.parse_example_files(last_message)
                if "readme.md" not in last_message.lower():
                    readme_section = self.handle_readme_generation(
                        last_message, step_messages
                    )
                    if readme_section:
                        code_files.update(readme_section)

                success, str_results = self.enforce_successful_sandbox_execution(
                    code_files
                )

                if success:
                    response = self.handle_code_files_pr_raise(
                        code_files, step_messages
                    )
                    return {"content": response}
                else:
                    step_messages += [{"role": "user", "content": str_results}]
                    continue

            return {"content": "Completed news stream processing, PR was not created."}
