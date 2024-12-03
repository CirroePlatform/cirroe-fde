from include.utils import get_git_image_links
from typing import List, Dict, Any
from src.core.event.user_actions.handle_base_action import BaseActionHandler
from src.model.issue import Issue
from dotenv import load_dotenv
from logger import logger
from uuid import UUID
import anthropic
import traceback
import base64
import httpx
import json
import time
import os

from src.integrations.kbs.base_kb import KnowledgeBaseResponse
from src.integrations.kbs.github_kb import Repository
from src.model.issue import OpenIssueRequest
from src.storage.supa import SupaClient
from src.core.tools import SearchTools
from include.constants import (
    DEBUG_ISSUE_FILE,
    DEBUG_TOOLS,
    DEBUG_ISSUE_FINAL_PROMPT,
    MODEL_HEAVY,
    ORG_NAME,
    REPO_NAME,
)

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


class HandleIssue(BaseActionHandler):
    def __init__(self, org_id: UUID):
        self.org_id = org_id

        userdata = SupaClient(user_id=self.org_id).get_user_data(
            ORG_NAME, REPO_NAME, debug=True
        )
        repo = Repository(
            remote="github.com", repository=userdata[REPO_NAME], branch="main"
        )
        search_tools = SearchTools(self.org_id, [repo])
        self.tools_map = {
            "execute_codebase_search": search_tools.execute_codebase_search,
            "execute_documentation_search": search_tools.execute_documentation_search,
            "execute_issue_search": search_tools.execute_issue_search,
        }

        super().__init__(
            anthropic.Anthropic(api_key=ANTHROPIC_API_KEY),
            DEBUG_ISSUE_FILE,
            DEBUG_TOOLS,
            self.tools_map,
            MODEL_HEAVY,
        )

    def construct_initial_messages(self, issue: Issue) -> List[Dict[str, Any]]:
        """
        Construct the initial message stream for the issue.

        Args:
            issue_content (str): The issue content to construct the message stream for

        Returns:
            List[Dict[str, Any]]: The initial message stream
        """
        issue_content = (
            issue.description
            + "\n\n"
            + "\n".join([comment.comment for comment in issue.comments])
        )
        image_links = get_git_image_links(issue_content)

        image_base64s = []
        for link in image_links:
            # Might get a redirect to an s3 bucket, so just need to follow it.
            response = httpx.get(link)
            if response.status_code == 302:
                response = httpx.get(response.headers["Location"])
            else:
                logger.error("Failed to get image from link: %s", link)
                continue

            media_type = response.headers["Content-Type"]
            img_data = base64.standard_b64encode(response.content).decode("utf-8")
            image_base64s.append((img_data, media_type))

        # Initialize message stream with issue description and any comments
        messages = [
            {"role": "user", "content": issue_content},
        ]

        if image_base64s:
            messages[0]["content"] = [
                {"type": "text", "text": messages[0]["content"]},
                *[
                    {
                        "type": "text",
                        "text": f"<comment>{json.dumps(comment.model_dump_json())}</comment>",
                    }
                    for comment in issue.comments
                ],
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

    def debug_issue(
        self, issue_req: OpenIssueRequest, max_tool_calls: int = 5
    ) -> Dict[str, Any]:
        """
        Given some issue, the agent will try to solve it using chain-of-thought reasoning
        and available tools to return a response comment to the issue.

        Args:
            issue_req: The issue request containing description and metadata
            max_tool_calls: Maximum number of tool calls allowed (default: 5)

        Returns:
            Dict containing the final response and collected KB responses
        """
        # Construct initial message stream
        messages = self.construct_initial_messages(issue_req.issue)
        response = self.handle_action(messages, max_tool_calls)

        if response["response"] and response["confidence_score"] > 50:
            return response

        # Generate final response with summarized data.
        try:
            # Load final prompt for summarization
            with open(DEBUG_ISSUE_FINAL_PROMPT, "r", encoding="utf8") as fp:
                final_sysprompt = fp.read()

            final_call = self.client.messages.create(
                model=MODEL_HEAVY,
                system=final_sysprompt,
                max_tokens=2048,
                messages=messages,
                temperature=0.1,
            )

            if (
                final_call.content
                and len(final_call.content) > 0
                and hasattr(final_call.content[0], "text")
                and "<failure>" not in final_call.content[0].text
            ):
                final_response = final_call.content[0].text
            else:
                logger.error(
                    "Failed to generate final response: %s",
                    (
                        final_call.content[0].text
                        if final_call.content and hasattr(final_call.content[0], "text")
                        else "No content"
                    ),
                )
                final_response = "Unable to generate a complete response. Please review the collected information."

            logger.info("Final response generated: %s", final_response)

            return {
                "response": final_response,
                "kb_responses": response["kb_responses"],
            }

        except Exception as e:
            logger.error("Error generating final response: %s", str(e))
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to generate final response: {str(e)}")
