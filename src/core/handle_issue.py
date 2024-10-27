from logger import logger
from contextvars import ContextVar
from typeguard import typechecked
from merge.resources.ticketing import CommentRequest
from merge.resources.ticketing import Ticket
from uuid import UUID
from typing import Dict, Any, Optional, List, Tuple
import anthropic
from dotenv import load_dotenv

from src.storage.vector import VectorDB, RUNBOOK
from src.model.issue import OpenIssueRequest

from src.core.executor import RunBookExecutor

from src.integrations.cloud import CloudIntegration
from src.integrations.merge import client as merge_client
from src.integrations.humanlayer_integration import hl

load_dotenv()

RUNBOOKS = {}  # {rid: runbook}

rb_executor = RunBookExecutor()
vector_db = VectorDB()

# Knowledge sources
CODEBASE = "codebase"  # TODO implement
DOCUMENTATION = "documentation"  # TODO implement
ISSUES = "issues"  # TODO implement
CLOUD = "cloud"  # TODO integrate cloud search here


COLLECTION_NAME_DESCRIPTION = f"""
The type of knowledge base to query over, this specifies which knowledge base we extract the top k chunks of data from.

The following are descriptions of the various knowledge bases, and the information they contain. Use these descriptions to decide
which knowledge base to query.

{RUNBOOK}: A runbook knowledge base that contains engineer defined runbooks that may pertain to some commonly known issues. The response would 
be a list of runbooks, which contains solution descriptions and commands.

{ISSUES}: This is a knowledge base of previous issues from users, the response here would contain a list of issues with comments and descriptions from 
users and engineers, and the whether the issue has been resolved.

{CLOUD}: A cloud knowledge base, will perform a search over the team's cloud environment for relevant metrics, logs, and other data.

{CODEBASE}: A codebase knowledge base. This will return the top k chunks of code from the teams codebase relevant to the issue.
"""
# {DOCUMENTATION}: Relevant data from the team's documentation will be returned with this collection.

DEBUG_ISSUE_TOOLS = [
    {
        "name": "solve_issue_with_collections",
        "description": "A function to get the top k similar chunks of data from various knowledge bases for identifying and triaging a customer issue",
        "input_schema": {
            "type": "object",
            "properties": {
                "problem_description": {
                    "type": "string",
                    "description": "A description of an issue from a customer on some ticket",
                },
                "collection_names": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "items": [
                            {
                                "type": "string",
                                "enum": [
                                    RUNBOOK,
                                    CODEBASE,
                                    # DOCUMENTATION,
                                    CLOUD,
                                    ISSUES,
                                ],
                                "description": COLLECTION_NAME_DESCRIPTION,
                            },
                            {
                                "type": "integer",
                                "minimum": 0,
                                "description": "The number of chunks to retrieve from the specific knowledge base",
                            },
                        ],
                    },
                    "description": "A list of tuples, each containing a collection name and the number of chunks to retrieve",
                },
            },
            "required": ["problem_description", "collection_names"],
        },
    }
]

DEBUG_ISSUE_FILE = "include/prompts/debug_issue.txt"

vector_db = VectorDB()
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
    issue_context: ContextVar = ContextVar('issue_context')
    issue_context.set(issue_req)

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        system=sysprompt,
        max_tokens=2048,
        tools=DEBUG_ISSUE_TOOLS,
        tool_choice={"type": "any"},
        messages=messages,
    )

    while response.stop_reason == "tool_use":
        response_message = response.content[0].input
        tool_name = response.content[0].name
        tool_call_id = response.content[0].id

        if tool_name:
            messages.append(
                response_message
            )  # extend conversation with assistant's reply
            # logger.info(
            #     "last message led to %s tool calls: %s",
            #     len(tool_name),
            #     [
            #         (tool_call.function.name, tool_call.function.arguments)
            #         for tool_call in tool_calls
            #     ],
            # )


            function_name = tool_name
            function_args = response_message
            function_response: str

            logger.info("CALL tool %s with %s", function_name, function_args)

            try:
                function_response = function_name(**function_args)
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
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            tools=DEBUG_ISSUE_TOOLS,
            messages=messages,
        )

    comment_on_ticket(issue_req.issue.tid, response.choices[0].message.content)
    logger.info("Comment added to ticket: %s", response.choices[0].message.content)

# Below are all anthropic tools.
@typechecked
def solve_issue_with_collections(
    problem_description: str, collection_names: List[Tuple[str, int]]
) -> Dict[str, Any]:
    """
    Top k similar knowledge bases and their distances.

    collection = knowledge base

    Returns a dict like so:
    ```json
    {
        "collection_name":
            [
                {
                    "similarity": float,
                    "metadata": {
                        // Some metadata, differs depending on the collection type.
                    }
                }
            ],
    }
    ```
    """
    rv = {}
    for collection_name, k in collection_names:
        logger.info("Agent chose collection %s with %d entries", collection_name, k)

        if collection_name == RUNBOOK:
            # query_vector = vector_db.model.encode(problem_description)
            # rv += vector_db.get_top_k_runbooks(k, query_vector)
            pass
        elif collection_name == ISSUES:
            pass # Pending merge API integration
        elif collection_name == CLOUD:
            execute_cloud_command(problem_description)
        elif collection_name == CODEBASE:
            pass # Pending codebase search integration
        # elif collection_name == DOCUMENTATION:
        #   pass # Pending documentation search integration
        else:
            raise ValueError(
                "Error, passed in an enum for some collection that dne: "
                + collection_name
            )

    return rv  # TODO make this string formatted? Or json should be ok.

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
    if provider not in ['aws', 'gcp', 'azure']:
        raise ValueError("Command must start with cloud provider: 'aws', 'gcp', or 'azure'")
        
    # Remove provider prefix from command
    command = ' '.join(command.split()[1:])
    
    # Get org_id from thread-local context set in debug_issue()
    issue_context: ContextVar = ContextVar('issue_context')
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

@hl.require_approval()
def resolve_ticket(comment: Optional[str] = None):
    """
    Resolves a ticket, requires engineer approval
    """
    pass
