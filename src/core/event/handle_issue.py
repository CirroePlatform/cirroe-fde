from logger import logger
from merge.resources.ticketing import CommentRequest
from merge.resources.ticketing import Ticket
from uuid import UUID
from typing import List
import anthropic
from dotenv import load_dotenv

from src.model.issue import OpenIssueRequest
from src.core.tools import SearchTools
from src.integrations.kbs.github_kb import Repository
from include.constants import MODEL_LIGHT, DEBUG_ISSUE_FILE, DEBUG_TOOLS

load_dotenv()

client = anthropic.Anthropic()


def debug_issue(issue_req: OpenIssueRequest, github_repos: List[Repository]) -> str:
    """
    Giiven some issue, the agent will try to solve it using the tools available to it and return a response of a comment to the issue.
    """

    with open(DEBUG_ISSUE_FILE, "r", encoding="utf8") as fp:
        sysprompt = fp.read()

    messages = [
        {"role": "user", "content": issue_req.issue.description},
    ]

    response = client.messages.create(
        model=MODEL_LIGHT,
        system=sysprompt,
        max_tokens=2048,
        tools=DEBUG_TOOLS,
        tool_choice={"type": "any"},
        messages=messages,
    )
    logger.info("Response: %s", response)

    search_tools = SearchTools(issue_req.requestor_id, github_repos)
    TOOLS_MAP = {
        "execute_codebase_search": search_tools.execute_codebase_search,
        "execute_documentation_search": search_tools.execute_documentation_search,
        "execute_issue_search": search_tools.execute_issue_search,
    }

    while response.stop_reason == "tool_use":
        response_message = response.content[0].input
        tool_name = response.content[0].name
        tool_call_id = response.content[0].id
        logger.info("Tool name: %s", tool_name)
        logger.info("Response message: %s", response_message)
        logger.info("Tool call id: %s", tool_call_id)

        if tool_name:
            messages.append(
                response_message
            )  # extend conversation with assistant's reply

            function_name = tool_name
            function_args = response_message
            function_response: str
            fn_to_call = TOOLS_MAP[function_name]

            logger.info("CALL tool %s with %s", function_name, function_args)

            try:
                function_response = fn_to_call(**function_args)
            except Exception as e:
                function_response = str(e)

            logger.info(
                "tool %s responded with %s",
                function_name,
                function_response[:200],
            )
            messages.append(
                {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response

        response = client.messages.create(
            model=MODEL_LIGHT,
            max_tokens=2048,
            tools=DEBUG_TOOLS,
            tool_choice={"type": "any"},
            messages=messages,
        )

        logger.info("Response: %s", response)

    logger.info(
        "Would've added comment to ticket: %s", response.choices[0].message.content
    )
    return response.choices[0].message.content


def index_all_issues_async(org_id: UUID):
    """
    Indexes all issues in the database.
    """
    raise NotImplementedError(
        "Not implemented the indexing all issues async for an org yet."
    )
