from typing import Dict, List, Any, Tuple
from src.model.issue import Issue, Comment
import asyncio
import json
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

    def debug_example(self, code_files: str) -> Dict[str, Any]:
        """
        Helper function to debug the example

        Args:
            code_files (str): The code files to debug

        Returns:
            Dict[str, Any]: The response from the debugger
        """
        with open("include/prompts/example_builder/example_debugger.txt", "r") as f:
            debugger_prompt = f.read()
            debugger_prompt_msgs = [
                {
                    "type": "text",
                    "text": format_prompt(debugger_prompt, product_name=self.product_name, preamble=self.preamble),
                    "cache_control": {"type": "ephemeral"}
                }
            ]

        # set tools to the debugger tools
        self.tools = EXAMPLE_CREATOR_DEBUGGER_TOOLS

        # Running the code sandbox once to enforce it.
        messages = [{"role": "user", "content": f"Here are the code files you need to work with:\n<code_files>{code_files}</code_files>"}]
        response = super().handle_action(
            messages,
            max_txt_completions=1,
            system_prompt=debugger_prompt_msgs,
            tool_choice={"type": "tool", "name": "run_code_e2b"}
        )

        response = super().handle_action(
            messages,
            max_txt_completions=10,
            system_prompt=debugger_prompt_msgs
        )

        return response

    def _cache_code_files(self, code_files: Dict[str, Any], title: str, description: str, commit_msg: str, branch_name: str) -> None:
        """
        Cache the code files dictionary to disk.

        Args:
            code_files: Dictionary containing the code files and their contents
        """

        cache_dir = "include/cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = f"{cache_dir}/code_files_cache.json"
        
        try:
            with open(cache_file, "w") as f:
                json.dump({
                    "code_files": code_files,
                    "title": title,
                    "description": description,
                    "commit_msg": commit_msg,
                    "branch_name": branch_name
                }, f)
        except Exception as e:
            logging.error(f"Failed to cache code files: {str(e)}")

    def _get_cached_code_files(self) -> Dict[str, Any]:
        """
        Read the cached code files from disk.

        Returns:
            Dict containing the cached code files, or empty dict if no cache exists
        """
        cache_file = "include/cache/code_files_cache.json"
        
        if not os.path.exists(cache_file):
            return {}
            
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to read cached code files: {str(e)}")
            return {}

    def _handle_pr_suggestions_output(self, response: Dict[str, Any], pr_webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the output of the PR suggestions tool. This should do the following:
            if the changed code is not false, then we need to cache the code files, and submit a revision to the PR.

            if the comment response is not false, then we need to respond to the PR with the comment response.

        sample response parameter:
        {
            response: 'I\'ll analyze the comment and the code to determine the appropriate action.\n\nThe comment suggests: "add a comment here explaining how you\'re doing the URL construction."\n\nLet\'s evaluate the suggestion:\n1. The comment is referring to this line: `urls=[f"https://www.google.com/search?q={query.replace(\' \', \'+\')}"]`\n2. The suggestion is to add a comment explaining how the URL is being constructed\n3. This is a stylistic change that will improve code readability\n\nI\'ll add a descriptive comment explaining the URL construction:\n\n<changed_code>\nexamples/job_market_intelligence_agent/job_market_agent.py\n@@ -20,7 +20,10 @@\n         results = []\n         for location in locations:\n             query = f"{job_title} jobs in {location}"\n-            scraped_data = self.firecrawl.crawl(\n+            # Construct a Google search URL by:\n+            # 1. Creating a search query string for job listings\n+            # 2. Replacing spaces with \'+\' for URL encoding\n+            scraped_data = self.firecrawl.crawl(\n                 urls=[f"https://www.google.com/search?q={query.replace(\' \', \'+\')}"],\n                 params={\n                     "extractors": {\n</changed_code>\n\n<comment_response>\nI\'ve added a comment explaining the URL construction process, detailing how the search query is transformed for use in a Google search URL. This helps clarify the code\'s intent and makes it more readable for other developers.\n</comment_response>\n\nThe comment provides context about:\n1. What the code is doing (creating a Google search URL)\n2. How it\'s modifying the query (replacing spaces with \'+\')\n3. The purpose of the modification (URL encoding)\n\nThis change improves code readability without changing the functionality of the code.'
        }
        
        Args:
            response: Dictionary containing response data including messages and final response
            
        Returns:
            Dict containing the processed response data
        """
        if not response or "response" not in response:
            return response
            
        final_response = response["response"]
        
        # Extract changed code and comment response using regex
        changed_code_pattern = r"<changed_code>\s*(.*?)\s*</changed_code>"
        comment_pattern = r"<comment_response>\s*(.*?)\s*</comment_response>"

        changed_code_match = re.search(changed_code_pattern, final_response, re.DOTALL)
        comment_match = re.search(comment_pattern, final_response, re.DOTALL)
        
        if not changed_code_match:
            return response

        # Extract file path and diff content
        changed_code = {}
        changed_code_content = changed_code_match.group(1)
        
        # Split the content by file paths, but keep the unified diff headers
        file_sections = re.split(r'\n(?=\w+/.*?\n@@)', changed_code_content)
        
        for section in file_sections:
            if not section.strip():
                continue
            # First line should be the file path
            lines = section.strip().split('\n', 1)
            if len(lines) < 2:
                continue
            file_path = lines[0].strip()
            # Keep the entire diff including the unified header
            file_diff = lines[1].strip()
            if not file_diff.startswith("@@"):
                continue
            changed_code[file_path] = file_diff

        comment_response = comment_match.group(1).strip() if comment_match else None

        # Handle changed code if not false
        if changed_code and all(diff.lower() != "false" for diff in changed_code.values()):
            # Cache the code files
            cached_code_files = self._get_cached_code_files()
            for file_path, file_diff in changed_code.items():
                original = cached_code_files["code_files"][file_path] if file_path in cached_code_files["code_files"] else ""
                cached_code_files["code_files"][file_path] = self.github_kb.apply_diff(original, file_diff)

            self._cache_code_files(cached_code_files, cached_code_files["title"], cached_code_files["description"], cached_code_files["commit_msg"], cached_code_files["branch_name"])

            # Submit the revision
            pr_number = pr_webhook_payload.get("number")
            title = cached_code_files["title"]
            description = cached_code_files["description"]
            commit_msg = cached_code_files["commit_msg"]
            branch_name = cached_code_files["branch_name"]
            self.sandbox.create_github_pr(changed_code, "Cirr0e/firecrawl-examples", title, description, commit_msg, branch_name, pr_number)

            response["changed_code"] = changed_code
            
        # Handle comment response if not false    
        if comment_response and comment_response.lower() != "false":
            # Submit the comment after crafting the parameters correctly
            comment_id = pr_webhook_payload.get("comment", {}).get("id")

            comment_on_pr("Cirr0e", "firecrawl-examples", comment_id, comment_response)
            response["comment_response"] = comment_response

        return response

    def handle_pr_feedback(self, feedback_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle feedback on a PR.

        Args:
            feedback_payload: The feedback payload from the PR. See below for an example.
        """
        with open("include/prompts/example_builder/handle_pr_suggestions.txt", "r") as f:
            handle_pr_suggestions_prompt = f.read()

            code_diff_fpath = feedback_payload.get("comment", {}).get("path")
            code_diff = feedback_payload.get("comment", {}).get("diff_hunk")
            comment = feedback_payload.get("comment", "")
            code_files = self._get_cached_code_files()

            handle_pr_suggestions_prompt = format_prompt(handle_pr_suggestions_prompt, preamble=self.preamble)
            first_message = f"""First, examine the following code diff where a comment is made:
                <code_diff_{code_diff_fpath}>
                {code_diff}
                </code_diff_{code_diff_fpath}>

                Now, review the comment metadata:

                <comment>
                {comment}
                </comment>

                And finally, here is the entire code example content:

                <code_files>
                {code_files}
                </code_files>
            """

            handle_pr_suggestions_prompt_msg = [{
                "type": "text",
                "text": handle_pr_suggestions_prompt,
                "cache_control": {"type": "ephemeral"}
            }]

            self.tools = EXAMPLE_CREATOR_PR_TOOLS

            response = super().handle_action(
                [{"role": "user", "content": first_message}],
                max_txt_completions=10,
                system_prompt=handle_pr_suggestions_prompt_msg
            )

            return self._handle_pr_suggestions_output(response, feedback_payload)

    def handle_readme_generation(self, code_files: str, step_messages: List[Dict[str, Any]]) -> Dict[str, str] | None:
        """
        Handle the generation of a README.md file based on the code files. 
        
        Returns the readme {path: content} dict, or None if the readme was not generated/couldn't be parsed.
        """
        readme_response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=step_messages + [{"role": "user", "content": f"Based on these code files, and previous messages, generate a README.md file:\n{code_files}"}],
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
            readme_section = get_content_between_tags(readme_content, readme_tag_start, readme_tag_end)
            readme_section = {
                readme_tag_start.split('fpath_')[1].split('>')[0]: readme_section
            }
            return readme_section

        return None

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
                # time.sleep(60) # Just so we don't overload the anthropic API
                continue

            if step_messages[-1]["role"] != "user":
                step_messages += [
                    {
                        "role": "user", 
                        "content": f"We've identified a need to perform the '{action}' action, now let's continue to develop the example based on all previous information."
                    }
                ]

            while max_tool_calls > 0:
                time.sleep(60)

                step_response = super().handle_action(step_messages, max_tool_calls, system_prompt=cur_prompt)
                last_message = step_response["response"]
                if ("<code_files>" in last_message):
                    # Append the final message with the files to the step messages.
                    code_files = get_content_between_tags(last_message, "<code_files>", "</code_files>")

                    # Debug the example and ensure clean execution. If the debug response is false, then the debugger didn't 
                    # modify the code, and we can keep the last message as the final message.
                    # debug_response = self.debug_example(code_files)
                    # if "<code_files>" in debug_response["response"]:
                    #     code_files_new = get_content_between_tags(debug_response["response"], "<code_files>", "</code_files>")
                    #     if code_files_new != "false":
                    #         code_files = code_files_new

                    # Enforce the creation of a README.md file
                    if "README.md" not in code_files:
                        readme_section = self.handle_readme_generation(code_files, step_messages)
                        if readme_section:
                            code_files.update(readme_section)

                    # Craft the PR title and body
                    title, description, commit_msg, branch_name = self.craft_pr_title_and_body(
                        step_messages,
                    )
                    response = self.sandbox.create_github_pr(
                        last_message,
                        # f"{self.org_name}/{self.product_name}", TODO: change this back after we finish mocking the demo
                        "Cirr0e/firecrawl-examples",
                        title,
                        description,
                        commit_msg,
                        branch_name,
                    )

                    # cache the code files for later...
                    codefiles = self.sandbox.parse_example_files(last_message)
                    self._cache_code_files(codefiles, title, description, commit_msg, branch_name)

                    return {"content": response}

                elif step_messages[-1]["role"] != "user":
                    logging.info("PR was not created because last message was not a user message. appending a continue message")
                    step_messages += [
                        {
                            "role": "user", 
                            "content": f"Given the previous messages, continue to develop the example based on all previous information. Make sure to wrap the code files in <code_files> tags."
                        }
                    ]
                else:
                    logging.info("PR was not created even though last message was not a user message.")
                    return {"content": "Completed news stream processing. PR was not created."}
            
            return {"content": "Completed news stream processing after reaching max tool calls. PR was not created."}
