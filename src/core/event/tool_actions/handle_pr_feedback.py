from typing import Dict, Any
from include.utils import format_prompt
import re
from include.constants import EXAMPLE_CREATOR_PR_TOOLS
from .handle_base_action import BaseActionHandler
from src.core.event.poll import comment_on_pr

class PrFeedbackHandler(BaseActionHandler):
    """
    Handles pr feedback from the github webhook
    """
    def _handle_pr_suggestions_output(
        self, response: Dict[str, Any], pr_webhook_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
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
        file_sections = re.split(r"\n(?=\w+/.*?\n@@)", changed_code_content)

        for section in file_sections:
            if not section.strip():
                continue
            # First line should be the file path
            lines = section.strip().split("\n", 1)
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
        if changed_code and all(
            diff.lower() != "false" for diff in changed_code.values()
        ):
            # Cache the code files
            cached_code_files = self._get_cached_code_files()
            for file_path, file_diff in changed_code.items():
                original = (
                    cached_code_files["code_files"][file_path]
                    if file_path in cached_code_files["code_files"]
                    else ""
                )
                cached_code_files["code_files"][file_path] = self.github_kb.apply_diff(
                    original, file_diff
                )

            # Submit the revision
            pr_number = pr_webhook_payload.get("number")
            title = cached_code_files["title"]
            description = cached_code_files["description"]
            commit_msg = cached_code_files["commit_msg"]
            branch_name = cached_code_files["branch_name"]
            self.sandbox.create_github_pr(
                changed_code,
                "Cirr0e/firecrawl-examples",
                title,
                description,
                commit_msg,
                branch_name,
                pr_number,
            )

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
        with open(
            "include/prompts/example_builder/handle_pr_suggestions.txt", "r"
        ) as f:
            handle_pr_suggestions_prompt = f.read()

            code_diff_fpath = feedback_payload.get("comment", {}).get("path")
            code_diff = feedback_payload.get("comment", {}).get("diff_hunk")
            comment = feedback_payload.get("comment", "")
            
            # TODO: read the code files from the actual github PR.

            handle_pr_suggestions_prompt = format_prompt(
                handle_pr_suggestions_prompt, preamble=self.preamble
            )
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

            handle_pr_suggestions_prompt_msg = [
                {
                    "type": "text",
                    "text": handle_pr_suggestions_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]

            self.tools = EXAMPLE_CREATOR_PR_TOOLS

            response = super().handle_action(
                [{"role": "user", "content": first_message}],
                max_txt_completions=10,
                system_prompt=handle_pr_suggestions_prompt_msg,
            )

            return self._handle_pr_suggestions_output(response, feedback_payload)