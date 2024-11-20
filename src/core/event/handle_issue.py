from logger import logger
from uuid import UUID
from typing import List, Dict, Any
import anthropic
import json
from dotenv import load_dotenv

from src.model.issue import OpenIssueRequest
from src.core.tools import SearchTools
from src.integrations.kbs.github_kb import Repository
from src.integrations.kbs.base_kb import KnowledgeBaseResponse
from include.constants import (
    DEBUG_ISSUE_FILE,
    DEBUG_TOOLS,
    DEBUG_ISSUE_FINAL_PROMPT,
    MODEL_LIGHT,
)
SOLUTION_TAG_OPEN = "<solution>"
SOLUTION_TAG_CLOSE = "</solution>"

load_dotenv()

client = anthropic.Anthropic()


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
    kb_responses: List[KnowledgeBaseResponse],
    messages: List[Dict[str, str]],
) -> None:
    """
    Handles the tool response and updates messages and KB responses accordingly.

    Args:
        tool_name: Name of the tool that was called
        function_response: Response from the tool
        kb_responses: List of knowledge base responses to update
        messages: List of message dictionaries to update
    """
    append_message(messages, "user", f"Results from {tool_name}: {function_response}")


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

    # Initialize message stream with issue description and any comments
    messages = [
        {"role": "user", "content": f"<user_issue>{issue_req.issue.description}</user_issue>\n<user_comments>{json.dumps(issue_req.issue.comments)}</user_comments>"},
    ]

    # Initialize tools and response tracking
    search_tools = SearchTools(issue_req.requestor_id, github_repos)
    kb_responses = []
    tool_calls_made = 0

    TOOLS_MAP = {
        "execute_codebase_search": search_tools.execute_codebase_search,
        "execute_documentation_search": search_tools.execute_documentation_search,
        "execute_issue_search": search_tools.execute_issue_search,
    }

    while tool_calls_made < max_tool_calls:
        try:
            response = client.messages.create(
                model=MODEL_LIGHT,
                system=sysprompt,
                max_tokens=2048,
                tools=DEBUG_TOOLS,
                tool_choice={"type": "auto"},
                messages=messages,
            )

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
                        kbres, function_response = TOOLS_MAP[tool_name](**tool_input)
                        kb_responses.extend(
                            [KnowledgeBaseResponse.model_validate(kb) for kb in kbres]
                        )
                        handle_tool_response(
                            tool_name, function_response, kb_responses, messages
                        )
                    except Exception as e:
                        logger.error("Tool execution error: %s", str(e))
                        append_message(
                            messages,
                            "assistant",
                            f"Encountered an error with {tool_name}. Let me try a different approach.",
                        )
                        function_response = str(e)
                        handle_tool_response(
                            tool_name, function_response, kb_responses, messages
                        )

                    tool_calls_made += 1

            # Check if we should continue
            if response.stop_reason != "tool_use":
                break

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
                    if SOLUTION_TAG_OPEN in content.text and SOLUTION_TAG_CLOSE in content.text:
                        final_response = content.text.split(SOLUTION_TAG_OPEN)[1].split(SOLUTION_TAG_CLOSE)[0].strip()
                    else:
                        final_response = content.text

                    break

        if not final_response:
            # Load final prompt for summarization
            with open(DEBUG_ISSUE_FINAL_PROMPT, "r", encoding="utf8") as fp:
                final_sysprompt = fp.read()

            if tool_calls_made >= max_tool_calls:
                final_sysprompt += "\n\nNote: Maximum tool calls reached. Please provide a response based on available information."

            final_call = client.messages.create(
                model=MODEL_LIGHT,
                system=final_sysprompt,
                max_tokens=1024,
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
        raise RuntimeError(f"Failed to generate final response: {str(e)}")
