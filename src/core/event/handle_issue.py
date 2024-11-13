from logger import logger
from uuid import UUID
from typing import List
import anthropic
from dotenv import load_dotenv

from src.model.issue import OpenIssueRequest
from src.core.tools import SearchTools
from src.integrations.kbs.github_kb import Repository
from src.integrations.kbs.base_kb import KnowledgeBaseResponse
from include.constants import (
    MODEL_HEAVY,
    DEBUG_ISSUE_FILE,
    DEBUG_TOOLS,
    DEBUG_ISSUE_FINAL_PROMPT,
    MODEL_LIGHT,
)

load_dotenv()

client = anthropic.Anthropic()


def debug_issue(
    issue_req: OpenIssueRequest, github_repos: List[Repository], max_tool_calls: int = 3
) -> str:
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
        max_tokens=1024,
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

    kb_responses = []
    while response.stop_reason == "tool_use":
        tool_calls = response.content[0]
        tool_name = tool_calls.name
        tool_call_id = tool_calls.id
        tool_input = tool_calls.input

        logger.info("Tool name: %s", tool_name)
        logger.info("Tool input: %s", tool_input)
        logger.info("Tool call id: %s", tool_call_id)

        if tool_name:

            # Sometimes, the search goes way off the rails. We don't want to call tools indefinitely.
            max_tool_calls -= 1
            if max_tool_calls <= 0:
                break

            # Add the assistant's message with their reasoning/request
            messages.append(
                {
                    "role": "assistant",
                    "content": f"I'll search using {tool_name} with the following parameters: {tool_input}",
                }
            )

            function_name = tool_name
            function_args = tool_input
            fn_to_call = TOOLS_MAP[function_name]

            try:
                kbres, function_response = fn_to_call(**function_args)
                kb_responses += [
                    KnowledgeBaseResponse.model_validate(kb) for kb in kbres
                ]
            except Exception as e:
                function_response = str(e)

            logger.info(
                "Tool %s responded with %s",
                function_name,
                function_response,
            )

            # Add the function response as a user message
            messages.append(
                {
                    "role": "user",
                    "content": f"Results from {tool_name}: {function_response}",
                }
            )

        response = client.messages.create(
            model=MODEL_LIGHT,
            max_tokens=1024,
            tools=DEBUG_TOOLS,
            tool_choice={"type": "any"},
            messages=messages,
        )

    # Second phase: Request final summarized response
    if max_tool_calls <= 0:
        try:
            if (
                response.stop_reason != "tool_use"
                and response.content
                and len(response.content) > 0
            ):
                final_response = response.content[0].text
            else:
                with open(DEBUG_ISSUE_FINAL_PROMPT, "r", encoding="utf8") as fp:
                    final_sysprompt = fp.read()

                if max_tool_calls <= 0:
                    final_sysprompt += "\n\nNote: We ran out of tools calls for this particular issue. Please try to provide a response based on the information provided. If you cannot provide a response, please answer with a simple <failure> tag."

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
                    and "<failure>" not in final_call.content[0].text
                ):
                    final_response = final_call.content[0].text
                else:
                    logger.error(
                        f"Failed to generate a final response, using fallback. Actual output: {final_call.content[0].text}"
                    )
                    final_response = "Unable to generate a final response. Please review the collected information."

            logger.info("Final response generated: %s", final_response)

            return {"response": final_response, "kb_responses": kb_responses}

        except Exception as e:
            logger.error("Error generating final response: %s", str(e))
            raise RuntimeError(f"Failed to generate final response: {str(e)}")


def index_all_issues_async(org_id: UUID):
    """
    Indexes all issues in the database.
    """
    raise NotImplementedError(
        "Not implemented the indexing all issues async for an org yet."
    )
