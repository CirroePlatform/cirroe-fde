from logger import logger
from contextvars import ContextVar
from typeguard import typechecked
from merge.resources.ticketing import CommentRequest
from merge.resources.ticketing import Ticket
from uuid import UUID
from typing import Dict, Any, Optional
import anthropic
from dotenv import load_dotenv

from src.model.issue import OpenIssueRequest, Issue

from src.integrations.github import GithubIntegration
from src.integrations.cloud import CloudIntegration
from src.integrations.merge import client as merge_client

load_dotenv()

# Knowledge sources
CODEBASE = "codebase"  # TODO implement
DOCUMENTATION = "documentation"  # TODO implement
ISSUES = "issues"  # TODO implement
CLOUD = "cloud"  # TODO integrate cloud search here

ISSUES_TOOL_DESCRIPTION = "This is a knowledge base of previous issues from users, the response here would contain a list of issues with comments and descriptions from users and engineers, and the whether the issue has been resolved."

# TODO implement the rest of the knowledge bases
# {CLOUD}: A cloud knowledge base, will perform a search over the team's cloud environment for relevant metrics, logs, and other data.
# {RUNBOOK}: A runbook knowledge base that contains engineer defined runbooks that may pertain to some commonly known issues. The response would
# be a list of runbooks, which contains solution descriptions and commands.
# {DOCUMENTATION}: Relevant data from the team's documentation will be returned with this collection.

# Below are all anthropic tools.

@typechecked
class SearchTools:

    def __init__(self, requestor_id: UUID):
        self.requestor_id = requestor_id

    def execute_codebase_search(self, problem_description: str, k: int) -> Dict[str, Any]:
        """
            Execute a command over git repos using the Greptile API integration.

        Args:
            problem_description (str): The search query in natural language format.
            k (int): The number of chunks to retrieve from the codebase

        Returns:
            Dict[str, Any]: Results of the search with matches found
        """
        # Initialize Github integration with org context
        github = GithubIntegration(org_id=self.requestor_id)

        # Execute search via Greptile API
        try:
            response = github.search_code(problem_description, k=k)
            return response
        except Exception as e:
            return {
                "response": response,
                "error": str(e),
            }

DEBUG_ISSUE_TOOLS = [
    {
        "name": "execute_codebase_search",
        "description": "A function to search the teams codebase for relevant code snippets. This will return the top k chunks of code from the teams various codebases relevant to the provided search query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "problem_description": {
                    "type": "string",
                    "description": "A description of an issue from a customer on some ticket",
                },
                "k": {
                    "type": "integer",
                    "description": "The number of chunks to retrieve from the codebase",
                },
            },
            "required": ["problem_description", "k"],
        },
    }
]

DEBUG_ISSUE_FILE = "include/prompts/debug_issue.txt"

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

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
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
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            tools=DEBUG_ISSUE_TOOLS,
            tool_choice={"type": "any"},
            messages=messages,
        )
        logger.info("Response: %s", response)

    comment_on_ticket(issue_req.issue.tid, response.choices[0].message.content)
    logger.info("Comment added to ticket: %s", response.choices[0].message.content)


def execute_cloud_command(command: str) -> Dict[str, Any]:
    """
    Execute a cloud command. The provider will be automatically determined from the command prefix.
    The command should start with the provider name, e.g. 'aws ...', 'gcp ...', or 'azure ...'

    Args:
        command (str): The cloud command to execute, prefixed with provider name

    Returns:
        Dict[str, Any]: Result of command execution with success, output and error fields

    Raises:
        ValueError: If command doesn't start with valid provider prefix
    """
    # Extract provider from command prefix
    provider = command.split()[0].lower()
    if provider not in ["aws", "gcp", "azure"]:
        raise ValueError(
            "Command must start with cloud provider: 'aws', 'gcp', or 'azure'"
        )

    # Remove provider prefix from command
    command = " ".join(command.split()[1:])

    # Get org_id from thread-local context set in debug_issue()
    issue_context: ContextVar = ContextVar("issue_context")
    issue = issue_context.get()

    cloud_integration = CloudIntegration(org_id=issue.org_id)
    return cloud_integration.execute_command(provider, command)


def comment_on_ticket(tid: UUID, comment: Optional[str] = None):
    """
    Add a comment to a ticket.
    """
    merge_client.ticketing.comments.create(
        model=CommentRequest(html_body=comment, ticket=Ticket(id=tid))
    )


def change_asignee(tid: UUID, new_asignee: UUID):
    pass
