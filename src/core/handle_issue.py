from logger import logger
from typing import Dict, Any
import anthropic
from dotenv import load_dotenv

from src.storage.vector import VectorDB, DEBUG_ISSUE_TOOLS
from src.model.issue import Issue, OpenIssueRequest

from src.core.executor import RunBookExecutor

load_dotenv()

RUNBOOKS = {}  # {rid: runbook}

rb_executor = RunBookExecutor()
vector_db = VectorDB()

# Knowledge sources
RUNBOOK = "runbook"
LOGGING = "logs" # TODO implement
CODEBASE = "codebase" # TODO implement
DOCUMENTATION = "documentation" # TODO implement
ISSUES = "issues" # TODO implement
METRICS = "metrics" # TODO integrate spike detection here


COLLECTION_NAME_DESCRIPTION = f"""
The type of knowledge base to query over, this specifies which knowledge base we extract the top k chunks of data from.

The following are descriptions of the various knowledge bases, and the information they contain. Use these descriptions to decide
which knowledge base to query.

{RUNBOOK}: A runbook knowledge base that contains engineer defined runbooks that may pertain to some commonly known issues. The response would 
be a list of runbooks, which contains solution descriptions and commands.

{ISSUES}: This is a knowledge base of previous issues from users, the response here would contain a list of issues with comments and descriptions from 
users and engineers, and the whether the issue has been resolved.
"""
# {METRICS}: A metric knowledge base, will return a list of spiky metrics given the current time and 


DEBUG_ISSUE_TOOLS = [
    {
        "name": "solve_issue_with_collections",
        "description": "A function to get the top k similar chunks of data from various knowledge bases for identifying and triaging a customer issue",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue": {
                    "type": "int",
                    "description": "The number of chunks to retrieve from the specific knowledge base"
                },
                "collection_name": {
                    "type": "string",
                    "enum": [RUNBOOK, LOGGING, CODEBASE, DOCUMENTATION, METRICS],
                    "description": COLLECTION_NAME_DESCRIPTION
                }
            }
        }
    },
    {
        
    },
    {
        
    },
]

DEBUG_ISSUE_FILE = "include/prompts/debug_issue.txt"

vector_db = VectorDB()
client = anthropic.Anthropic()

from src.storage.vector import VectorDB

def debug_issue(issue_req: OpenIssueRequest, debug: bool = False) -> str:
    """
    Given a set of responses from executing some runbook, the issue from the user,
    and the runbook used, coalesce one final response to the user.
    """
    if debug:
        return "Nothing for now..."

    with open(DEBUG_ISSUE_FILE, "r", encoding="utf8") as fp:
        sysprompt = fp.read()

        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            tools=DEBUG_ISSUE_TOOLS,
            tool_choice={"type": "any", "name": "solve_issue_with_collections"},
            messages=[
                {"role": "system", "content": sysprompt},
                {"role": "user", "content": issue_req.issue.problem_description}
            ],
        )

        return response.choices[0].message.content

def solve_issue_with_collections(
    problem_description: str, collection_names: Dict[str, int]
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
    return rv # TODO make this string formatted? Or json should be ok.
