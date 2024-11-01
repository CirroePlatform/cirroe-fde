from logger import logger
from contextvars import ContextVar
from merge.resources.ticketing import CommentRequest
from merge.resources.ticketing import Ticket
from uuid import UUID
from typing import Dict, Any, Optional
import anthropic
from dotenv import load_dotenv

from src.model.issue import OpenIssueRequest, Issue
from src.core.tools import DEBUG_ISSUE_TOOLS, DEBUG_ISSUE_FILE, SearchTools
from src.integrations.merge import client as merge_client

MODEL_LIGHT = "claude-3-haiku-20240307"
MODEL_HEAVY = "claude-3-5-sonnet-20240620"

load_dotenv()

client = anthropic.Anthropic()

def debug_issue(issue_req: OpenIssueRequest, debug: bool = False):
    """
    Uses anthropic function calling to comment on an issue from a ticket a user opens.
    """
    if debug:
        return "Nothing for now..."

    with open(DEBUG_ISSUE_FILE, "r", encoding="utf8") as fp:
        sysprompt = fp.read()

    messages = [
        {"role": "user", "content": issue_req.issue.problem_description},
    ]

    # Set the issue context for the duration of this function call
    org_id_context: ContextVar[UUID] = ContextVar('org_id')
    org_id_context.set(issue_req.requestor_id)
    
    raise Exception("Not implemented, need to fetch the relevant org name from the integration")

    response = client.messages.create(
        model=MODEL_LIGHT,
        system=sysprompt,
        max_tokens=2048,
        tools=DEBUG_ISSUE_TOOLS,
        tool_choice={"type": "any"},
        messages=messages,
    )
    logger.info("Response: %s", response)

    search_tools = SearchTools(issue_req.requestor_id)
    TOOLS_MAP = {
        "execute_codebase_search": search_tools.execute_codebase_search,
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

            # try:
            function_response = fn_to_call(**function_args)
            # except Exception as e:
                # function_response = str(e)

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
            tools=DEBUG_ISSUE_TOOLS,
            tool_choice={"type": "any"},
            messages=messages,
        )
        logger.info("Response: %s", response)

    comment_on_ticket(issue_req.issue.tid, response.choices[0].message.content)
    logger.info("Comment added to ticket: %s", response.choices[0].message.content)


def comment_on_ticket(tid: UUID, comment: Optional[str] = None):
    """
    Add a comment to a ticket.
    """
    merge_client.ticketing.comments.create(
        model=CommentRequest(html_body=comment, ticket=Ticket(id=tid))
    )