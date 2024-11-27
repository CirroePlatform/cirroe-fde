from include.utils import get_git_image_links
from typing import List, Dict, Any
from src.model.issue import Issue
from dotenv import load_dotenv
from logger import logger
import anthropic
import traceback
import requests
import base64
import httpx
import json
import time
import os

from src.integrations.kbs.base_kb import KnowledgeBaseResponse
from src.integrations.kbs.github_kb import Repository
from src.model.issue import OpenIssueRequest
from src.core.tools import SearchTools
from include.constants import (
    DEBUG_ISSUE_FILE,
    DEBUG_TOOLS,
    DEBUG_ISSUE_FINAL_PROMPT,
    MODEL_HEAVY,
)

SOLUTION_TAG_OPEN = "<solution>"
SOLUTION_TAG_CLOSE = "</solution>"

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def append_message(messages: List[Dict[str, str]], role: str, content: str) -> None:
    """
    Appends a message to the message stream.

    Args:
        messages: List of message dictionaries
        role: Role of the message sender ('assistant' or 'user')
        content: The message content to append

    Returns:
        {"response": final_response, "kb_responses": kb_responses}

    """
    messages.append({"role": role, "content": content})


def handle_tool_response(
    tool_name: str,
    function_response: str,
    messages: List[Dict[str, str]],
) -> None:
    """
    Handles the tool response and updates messages and KB responses accordingly.

    Args:
        tool_name: Name of the tool that was called
        function_response: Response from the tool
        messages: List of message dictionaries to update
    """
    append_message(messages, "user", f"Results from {tool_name}: {function_response}")


def construct_initial_messages(issue: Issue) -> List[Dict[str, Any]]:
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
    issue_req: OpenIssueRequest, github_repos: List[Repository], max_tool_calls: int = 3
) -> Dict[str, Any]:
    """
    Given some issue, the agent will try to solve it using chain-of-thought reasoning
    and available tools to return a response comment to the issue.

    Args:
        issue_req: The issue request containing description and metadata
        github_repos: List of GitHub repositories to search
        max_tool_calls: Maximum number of tool calls allowed (default: 3)

    Returns:
        Dict containing the final response and collected KB responses
    """
    # Load system prompt
    with open(DEBUG_ISSUE_FILE, "r", encoding="utf8") as fp:
        sysprompt = fp.read()

    # Construct initial message stream
    messages = construct_initial_messages(issue_req.issue)

    # Initialize tools and response tracking
    search_tools = SearchTools(issue_req.requestor_id, github_repos)
    kb_responses = []
    tool_calls_made = 0

    TOOLS_MAP = {
        "execute_codebase_search": search_tools.execute_codebase_search,
        "execute_documentation_search": search_tools.execute_documentation_search,
        "execute_issue_search": search_tools.execute_issue_search,
    }

    response = client.messages.create(
        model=MODEL_HEAVY,
        system=sysprompt,
        max_tokens=2048,
        tools=DEBUG_TOOLS,
        tool_choice={"type": "auto"},
        messages=messages,
    )
    while tool_calls_made < max_tool_calls:
        try:
            # Handle the response content
            if not response.content:
                break

            for content in response.content:
                # Check if it's a text thought
                if hasattr(content, "text"):
                    append_message(messages, "assistant", content.text)
                    continue

                # Check if it's a tool call
                if hasattr(content, "name") and hasattr(content, "input"):
                    tool_name = content.name
                    tool_input = content.input

                    logger.info("Tool name: %s", tool_name)
                    logger.info("Tool input: %s", tool_input)

                    if not tool_name or tool_name not in TOOLS_MAP:
                        append_message(
                            messages,
                            "assistant",
                            "Invalid tool requested. Let me reconsider my approach.",
                        )
                        continue

                    # Execute tool call
                    try:
                        _, function_response = TOOLS_MAP[tool_name](
                            **tool_input
                        )  # TODO use kbres only, not the function response.
                        # kb_responses.extend(
                        #     [KnowledgeBaseResponse.model_validate(kb) for kb in kbres]
                        # )
                        handle_tool_response(tool_name, function_response, messages)
                    except Exception as e:
                        logger.error("Tool execution error: %s", str(e))
                        append_message(
                            messages,
                            "assistant",
                            f"Encountered an error with {tool_name}. Let me try a different approach.",
                        )
                        function_response = str(e)
                        handle_tool_response(tool_name, function_response, messages)

                    tool_calls_made += 1

            # Check if we should continue
            if response.stop_reason != "tool_use":
                break

            response = client.messages.create(
                model=MODEL_HEAVY,
                system=sysprompt,
                max_tokens=2048,
                tools=DEBUG_TOOLS,
                tool_choice={"type": "auto"},
                messages=messages,
            )
            time.sleep(75)  # TODO remove this. It's so we don't get rate limited by anthropic. Currently not able to call over 20k toks per minute.

        except Exception as e:
            logger.error("Error in main loop: %s", str(e))
            append_message(
                messages,
                "assistant",
                "Encountered an unexpected error. Let me try to formulate a response with the information I have.",
            )
            break

    # Generate final response
    try:
        # Check if we already have a final response
        final_response = None
        if response.stop_reason != "tool_use" and response.content:
            for content in response.content:
                if hasattr(content, "text"):
                    if (
                        SOLUTION_TAG_OPEN in content.text
                        and SOLUTION_TAG_CLOSE in content.text
                    ):
                        final_response = (
                            content.text.split(SOLUTION_TAG_OPEN)[1]
                            .split(SOLUTION_TAG_CLOSE)[0]
                            .strip()
                        )
                    break

        if not final_response:
            # Load final prompt for summarization
            with open(DEBUG_ISSUE_FINAL_PROMPT, "r", encoding="utf8") as fp:
                final_sysprompt = fp.read()

            if tool_calls_made >= max_tool_calls:
                final_sysprompt += "\n\nNote: Maximum tool calls reached. Please provide a response based on available information."

            final_call = client.messages.create(
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
        return {"response": final_response, "kb_responses": kb_responses}

    except Exception as e:
        logger.error("Error generating final response: %s", str(e))
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to generate final response: {str(e)}")
