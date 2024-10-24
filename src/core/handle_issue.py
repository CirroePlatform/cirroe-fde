from logger import logger
from typeguard import typechecked
from merge.resources.ticketing import CommentRequest
from merge.resources.ticketing import Ticket
from uuid import UUID
from typing import Dict, Any, Optional, List, Tuple
import anthropic
import json
from dotenv import load_dotenv

from src.storage.vector import VectorDB, RUNBOOK
from src.model.issue import OpenIssueRequest

from src.core.executor import RunBookExecutor

from src.integrations.merge import client as merge_client
from src.integrations.humanlayer_integration import hl

load_dotenv()

RUNBOOKS = {}  # {rid: runbook}

rb_executor = RunBookExecutor()
vector_db = VectorDB()

# Knowledge sources
LOGGING = "logs"  # TODO implement
CODEBASE = "codebase"  # TODO implement
DOCUMENTATION = "documentation"  # TODO implement
ISSUES = "issues"  # TODO implement
METRICS = "metrics"  # TODO integrate spike detection here


COLLECTION_NAME_DESCRIPTION = f"""
The type of knowledge base to query over, this specifies which knowledge base we extract the top k chunks of data from.

The following are descriptions of the various knowledge bases, and the information they contain. Use these descriptions to decide
which knowledge base to query.

{RUNBOOK}: A runbook knowledge base that contains engineer defined runbooks that may pertain to some commonly known issues. The response would 
be a list of runbooks, which contains solution descriptions and commands.

{ISSUES}: This is a knowledge base of previous issues from users, the response here would contain a list of issues with comments and descriptions from 
users and engineers, and the whether the issue has been resolved.

{METRICS}: A metric knowledge base, will return a list of spiky metrics for the provided issue.

{CODEBASE}: A codebase knowledge base. This will return the top k chunks of code from the teams codebase relevant to the issue.

{LOGGING}: A knowledge base of a set of logs from the team's logging system.

{DOCUMENTATION}: Relevant data from the team's documentation will be returned with this collection.
"""

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
                                    LOGGING,
                                    CODEBASE,
                                    DOCUMENTATION,
                                    METRICS,
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

HARDCODED_COMMENTS_RESPONSES = [
    "Checked and verified that we were suffering from overloaded CPU utilizations. Looked at all deployments on October 20th, seeing one that introduced potentially compute intensive code: https://github.com/AbhigyaWangoo/Hermes/commit/334023fa55d83d558688816c82f2eaf4eb26382e",
    """Engaging teammate to rollback change, will require the revert of that commit as well as any dependany commits that followed.""",
    "For future reference, please do not include print/debugging statements in production code pointlessly, they can cause significant spikes in cpu utilization.",
]

comment_idx = 0


def debug_issue(issue_req: OpenIssueRequest, debug: bool = False):
    """
    Uses anthropic function calling to comment on an issue from a ticket a user opens.
    """
    global comment_idx

    if debug:
        return "Nothing for now..."

    comment = HARDCODED_COMMENTS_RESPONSES[comment_idx]
    comment_idx = (comment_idx + 1) % len(HARDCODED_COMMENTS_RESPONSES)

    comment_on_ticket(issue_req.issue.tid, comment)
    logger.info("Comment added to ticket: %s", comment)


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
            query_vector = vector_db.model.encode(problem_description)
            rv += vector_db.get_top_k_runbooks(k, query_vector)
            pass
        elif collection_name == ISSUES:
            pass
        elif collection_name == METRICS:
            pass
        elif collection_name == DOCUMENTATION:
            pass
        elif collection_name == CODEBASE:
            pass
        elif collection_name == LOGGING:
            pass
        else:
            raise ValueError(
                "Error, passed in an enum for some collection that dne: "
                + collection_name
            )

    return rv  # TODO make this string formatted? Or json should be ok.


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
